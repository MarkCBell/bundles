#include <Python.h>
#include "structmember.h"
#include <vector>
#include <string>
#include <map>

#if PY_MAJOR_VERSION < 3
	#define int_test PyInt_Check
	#define int_convert PyInt_AsLong
	#define int_deconvert PyInt_FromLong
	
	#define string_convert PyString_AsString
	#define string_deconvert PyString_FromString
	
#else
	#define int_test PyLong_Check
	#define int_convert PyLong_AsLong
	#define int_deconvert PyLong_FromLong
	
	#define string_convert PyBytes_AsString
	#define string_deconvert PyBytes_FromString
#endif

typedef struct 
{
	PyObject_HEAD
	std::string* alphabet;
	int alphabet_len;
	std::map<char,int>* alphabet_lookup;
	
	PyObject* Py_machine;
	PyObject* Py_yield_states;
	
	// std::vector<int>* machine;
	int* machine;
	int num_states;
	std::vector<PyObject*>* yield_info;
	std::vector<int>* yield_len;
} c_FSM;

static void c_FSM_dealloc(c_FSM* self)
{
	delete self->alphabet;
	// self->alphabet_len = 0;
	delete self->alphabet_lookup;
	
	Py_DECREF(self->Py_machine);
	Py_DECREF(self->Py_yield_states);
	
	// delete self->machine;
	delete[] self->machine;
	// self->num_states = 0;
	delete self->yield_info;
	delete self->yield_len;
	
	Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject* c_FSM_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	c_FSM* self = (c_FSM *)type->tp_alloc(type, 0);
	if (self == NULL)
		return NULL;
	
	self->alphabet = NULL;
	self->alphabet_len = 0;
	self->alphabet_lookup = NULL;
	
	self->Py_machine = NULL;
	self->Py_yield_states = NULL;
	
	self->machine = NULL;
	self->num_states = 0;
	self->yield_info = NULL;
	self->yield_len = NULL;
	
	return (PyObject*) self;
}

static int c_FSM_init(c_FSM *self, PyObject *args, PyObject *kwds)
{
	const char* temp;
	if (!PyArg_ParseTuple(args, "sOO", &temp, &(self->Py_machine), &(self->Py_yield_states)))
		return NULL;
	
	self->alphabet = new std::string(temp);
	self->alphabet_len = self->alphabet->length();
	self->alphabet_lookup = new std::map<char,int>;
	
	for (int i =0; i < self->alphabet_len; i++)
		(*self->alphabet_lookup)[self->alphabet->at(i)] = i;
	
	int item_list_len = PySequence_Length(self->Py_machine);
	// self->machine = new std::vector<int> (item_list_len, -1);
	self->machine = new int[item_list_len];
	
	for (int i = 0; i < item_list_len; i++)
	{
		PyObject* item = PySequence_GetItem(self->Py_machine, i);
		if (! int_test(item))
		{
			PyErr_SetString(PyExc_TypeError, "Expected sequence of integers.");
			return NULL;
		}
		// self->machine->at(i) = int_convert(item);
		self->machine[i] = int_convert(item);
		Py_DECREF(item);
	}
	// self->num_states = item_list_len / self->alphabet_len;
	self->num_states = item_list_len / self->alphabet_len;
	
	int item_list_len2 = PySequence_Length(self->Py_yield_states);
	self->yield_info = new std::vector<PyObject*> (item_list_len2, NULL);
	self->yield_len = new std::vector<int> (item_list_len2, 0);
	
	for (int i = 0; i < item_list_len2; i++)
	{
		PyObject* item = PySequence_GetItem(self->Py_yield_states, i);
		self->yield_info->at(i) = item;
		self->yield_len->at(i) = PySequence_Length(item);
		Py_DECREF(item);
	}
	
	Py_INCREF(self->Py_machine);
	Py_INCREF(self->Py_yield_states);
	
	return 0;
}

static PyMemberDef c_FSM_members[] = 
{
	{NULL}  /* Sentinel */
};

static PyObject* c_FSM_evaluate(c_FSM* self, PyObject* args)
{
	const char* word;
	int quick_exit_temp = 1;  // Default true.
	
	if (! PyArg_ParseTuple(args, "s|i", &word, &quick_exit_temp))
		return NULL;
	
	bool quick_exit = (quick_exit_temp != 0);
	int word_len = strlen(word);
	PyObject* matches = (quick_exit) ? NULL : PyList_New(0);
	
	int state = 0;
	for (int i = 0; i < word_len; i++)
	{
		std::map<char,int>::iterator it = self->alphabet_lookup->find(word[i]);
		// state = (it == self->alphabet_lookup->end()) ? 0 : self->machine->at(state * self->alphabet_len + it->second);
		state = (it == self->alphabet_lookup->end()) ? 0 : self->machine[state * self->alphabet_len + it->second];
		
		if (state < 0)
			break;
		
		if (self->yield_len->at(state) > 0)
		{
			if (quick_exit)
			{
				return int_deconvert(-1);
			}
			else
			{
				for (int j = 0; j < self->yield_len->at(state); j++)
				{
					PyObject* item = PySequence_GetItem(self->yield_info->at(state), j);
					PyObject* new_item = Py_BuildValue("iO", i+1, item);
					Py_DECREF(item);
					PyList_Append(matches, new_item);
					Py_DECREF(new_item);
				}
			}
		}
	}
	
	return (quick_exit) ? int_deconvert(state) : matches;
}

static PyObject* c_FSM_has_cycle(c_FSM* self, PyObject* args)
{
	const char* word;
	int depth = -1;
	
	if (! PyArg_ParseTuple(args, "s|i", &word, &depth))
		return NULL;
	
	if (depth < 0 || depth > self->num_states)
		depth = self->num_states;
	
	// Check the string once.
	int word_len = strlen(word);
	
	// std::string str_word = std::string(word);
	// if (str_word.find_first_not_of(*self->alphabet) != std::string::npos)
	// {
		// PyErr_SetString(PyExc_TypeError, "Non-evaluatable letter present in cycle word.");
		// return NULL;
	// }
	
	int* converted_word = new int[word_len];
	for (int i = 0; i < word_len; i++)
	{
		std::map<char,int>::iterator it = self->alphabet_lookup->find(word[i]);
		if (it == self->alphabet_lookup->end())
		{
			PyErr_SetString(PyExc_TypeError, "Non-evaluatable letter present in cycle word.");
			delete[] converted_word;
			return NULL;
		}
		converted_word[i] = it->second;
	}
	
	for (int c = 0; c < depth; c++)
	{
		int state = c;
		for (int i = 0; i < word_len; i++)
		{
			// state = self->machine->at(state * self->alphabet_len + converted_word[i]);
			state = self->machine[state * self->alphabet_len + converted_word[i]];
			if (state < 0)
				break;
		}
		
		if (state == c)
		{
			delete[] converted_word;
			Py_RETURN_TRUE;
		}
	}
	
	delete[] converted_word;
	Py_RETURN_FALSE;
}

// We need these for pickling / unpickling which is essential for
// allowing this type to be passed to other processes.
static PyObject* c_FSM___getstate__(c_FSM* self, PyObject* args)
{
	return Py_BuildValue("(sOO)", (char*) self->alphabet->c_str(), self->Py_machine, self->Py_yield_states);
}

static PyObject* c_FSM___setstate__(c_FSM* self, PyObject* args)
{
	PyObject* new_args = PySequence_GetItem(args, 0);
	c_FSM_init(self, new_args, NULL);
	Py_DECREF(new_args);
	
	return Py_BuildValue("");
}

static PyMethodDef c_FSM_methods[] = {
	{"evaluate", (PyCFunction)c_FSM_evaluate, METH_VARARGS, "Evaluates the FSM on a string."},
	{"has_cycle", (PyCFunction)c_FSM_has_cycle, METH_VARARGS, "Determines if the FSM has a cycle on a string."},
	{"__getstate__", (PyCFunction)c_FSM___getstate__, METH_NOARGS, "For pickling."},
	{"__setstate__", (PyCFunction)c_FSM___setstate__, METH_VARARGS, "For depickling."},
	{NULL}  /* Sentinel */
};

static PyTypeObject c_FSM_Type = {
	PyObject_HEAD_INIT(NULL)
#if PY_MAJOR_VERSION < 3
	0,                         /*ob_size*/
#endif
	"c_FSM.c_FSM",               /*tp_name*/
	sizeof(c_FSM),              /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	(destructor)c_FSM_dealloc,  /*tp_dealloc*/
	0,                         /*tp_print*/
	0,                         /*tp_getattr*/
	0,                         /*tp_setattr*/
	0,                         /*tp_compare*/
	0,                         /*tp_repr*/
	0,                         /*tp_as_number*/
	0,                         /*tp_as_sequence*/
	0,                         /*tp_as_mapping*/
	0,                         /*tp_hash */
	0,                         /*tp_call*/
	0,                         /*tp_str*/
	0,                         /*tp_getattro*/
	0,                         /*tp_setattro*/
	0,                         /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,  /*tp_flags*/
	"A C++ implementation of a FSM.",          /* tp_doc */
	0,                         /* tp_traverse */
	0,                         /* tp_clear */
	0,                         /* tp_richcompare */
	0,                         /* tp_weaklistoffset */
	0,                         /* tp_iter */
	0,                         /* tp_iternext */
	c_FSM_methods,              /* tp_methods */
	c_FSM_members,              /* tp_members */
	0,                         /* tp_getset */
	0,                         /* tp_base */
	0,                         /* tp_dict */
	0,                         /* tp_descr_get */
	0,                         /* tp_descr_set */
	0,                         /* tp_dictoffset */
	(initproc)c_FSM_init,       /* tp_init */
	0,                         /* tp_alloc */
	c_FSM_new,                  /* tp_new */
};

static PyMethodDef module_methods[] = {
    {NULL}  /* Sentinel */
};

static char c_FSM_core_module_doc[] = "This module contains a C++ implementation of a FSM.";

#if PY_MAJOR_VERSION < 3
	PyMODINIT_FUNC initc_FSM_core(void) 
	{
		if (PyType_Ready(&c_FSM_Type) < 0)
			return;
		
		PyObject* m = Py_InitModule3("c_FSM_core", module_methods, c_FSM_core_module_doc);
		
		if (m == NULL)
			return;
		
		Py_INCREF(&c_FSM_Type);
		PyModule_AddObject(m, "c_FSM", (PyObject *)&c_FSM_Type);
	}
#else
	static PyModuleDef c_FSMmodule = {PyModuleDef_HEAD_INIT, "c_FSM", c_FSM_core_module_doc, -1, NULL, NULL, NULL, NULL, NULL};
	
	PyMODINIT_FUNC PyInit_c_FSM_core(void) 
	{
		c_FSM_Type.tp_new = PyType_GenericNew;
		if (PyType_Ready(&c_FSM_Type) < 0)
			return NULL;
		
		PyObject* m = PyModule_Create(&c_FSMmodule);
		if (m == NULL)
			return NULL;
		
		Py_INCREF(&c_FSM_Type);
		PyModule_AddObject(m, "c_FSM", (PyObject *)&c_FSM_Type);
		return m;
	}
#endif