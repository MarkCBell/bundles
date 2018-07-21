#include <Python.h>
#include "structmember.h"
#include <vector>
#include <string>

#if PY_MAJOR_VERSION < 3
	#define int_test PyInt_Check
	#define int_convert PyInt_AsLong
	#define int_deconvert PyInt_FromLong
	
	#define string_test PyString_Check
#else
	#define int_test PyLong_Check
	#define int_convert PyLong_AsLong
	#define int_deconvert PyLong_FromLong
	
	#define string_test PyUnicode_Check
#endif

typedef std::vector<char> translator;

translator* build_translator(const char* A, const char* B, int len)
{
	translator* V = new translator(256, 0);
	for (int i = 0; i < len; i++)
		V->at(A[i]) = B[i];
	
	return V;
}

char* translate(translator* T, const char* W, int len)
{
	char* W2 = new char[len+1];
	W2[len] = 0;
	
	for (int i = 0; i < len; i++)
		W2[i] = T->at(W[i]);
	
	return W2;
}

bool is_cyclic_ordered(const char* A, const char* B, int len)
{
	for (int i = 0; i < len; i++)
		for (int j = 0, k = i; j < len; j++, k++)
		{
			if (k >= len)
				k -= len;
			
			if (A[j] < B[k])
				break;
			
			if (A[j] > B[k])
				return false;
		}
	
	return true;
}

bool is_cyclic_ordered_reversed(const char* A, const char* B, int len)
{
	for (int i = 0; i < len; i++)
		for (int j = 0, k = i; j < len; j++, k--)
		{
			if (k < 0)
				k += len;
			
			if (A[j] < B[k])
				break;
			
			if (A[j] > B[k])
				return false;
		}
	
	return true;
}

bool check_automorph(bool symmetric_generators, translator* swapcase, translator* T, const char* word, const char* next_word, int len)
{
	char* w = translate(T, next_word, len);
	
	if (! is_cyclic_ordered(word, w, len))
	{
		delete w;
		return false;
	}
	
	if (symmetric_generators && !is_cyclic_ordered_reversed(word, w, len))
	{
		delete w;
		return false;
	}
	
	char* w2 = translate(swapcase, w, len);
	delete w;
	
	if (symmetric_generators && !is_cyclic_ordered(word, w2, len))
	{
		delete w2;
		return false;
	}
	
	if (! is_cyclic_ordered_reversed(word, w2, len))
	{
		delete w2;
		return false;
	}
	
	delete w2;
	
	return true;
}

const char* get_string(PyObject* PyString)
{
	PyObject* Py_temp_O = Py_BuildValue("(O)", PyString);
	const char* W;
	PyArg_ParseTuple(Py_temp_O, "s", &W);
	Py_DECREF(Py_temp_O);
	
	return W;
}


typedef struct 
{
	PyObject_HEAD
	
	bool symmetric_generators;
	std::string* alphabet;
	std::string* alphabet_swapcase;
	int alphabet_len;
	int alphabet_lower_len;
	translator* swapcase;
	
	PyObject* Py_automorphisms_always;
	PyObject* Py_automorphisms_missing;
	
	std::vector<int>* alphabet_indices;
	std::vector< translator* >* automorphisms_always;
	std::vector< translator* >* automorphisms_missing;
	std::vector<int>* automorphisms_missing_indices;
	int automorphisms_always_size;
	int automorphisms_missing_size;
	
} c_automorph;

static void c_automorph_dealloc(c_automorph* self)
{
	// self->symmetric_generators = false;
	delete self->alphabet;
	delete self->swapcase;
	// self->alphabet_len = 0;
	// self->alphabet_lower_len = 0;
	
	if (self->Py_automorphisms_always != NULL) Py_DECREF(self->Py_automorphisms_always);
	if (self->Py_automorphisms_missing != NULL) Py_DECREF(self->Py_automorphisms_missing);
	
	delete self->alphabet_indices;
	delete self->automorphisms_always;
	delete self->automorphisms_missing;
	delete self->automorphisms_missing_indices;
	// automorphisms_always_size = 0;
	// automorphisms_missing_size = 0;
	
	Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject* c_automorph_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	c_automorph* self = (c_automorph *)type->tp_alloc(type, 0);
	if (self == NULL)
		return NULL;
	
	self->symmetric_generators = true;
	self->alphabet = NULL;
	self->alphabet_len = 0;
	self->alphabet_lower_len = 0;
	self->swapcase = NULL;
	
	self->Py_automorphisms_always = NULL;
	self->Py_automorphisms_missing = NULL;
	
	self->alphabet_indices = NULL;
	self->automorphisms_always = NULL;
	self->automorphisms_missing = NULL;
	self->automorphisms_missing_indices = NULL;
	
	return (PyObject*) self;
}

static int c_automorph_init(c_automorph *self, PyObject *args, PyObject *kwds)
{
	const char* temp_alphabet;
	const char* temp_swapcase;
	int symmetric_generators_temp;
	if (!PyArg_ParseTuple(args, "issOO", &symmetric_generators_temp, &temp_alphabet, &temp_swapcase, &(self->Py_automorphisms_always), &(self->Py_automorphisms_missing)))
		return NULL;
	
	self->symmetric_generators = (symmetric_generators_temp != 0);
	
	self->alphabet = new std::string(temp_alphabet);
	self->alphabet_swapcase = new std::string(temp_swapcase);
	self->alphabet_len = self->alphabet->length();
	
	self->swapcase = build_translator(temp_alphabet, temp_swapcase, self->alphabet_len);
	
	// Build the alphabet lookup.
	self->alphabet_lower_len = 0;
	self->alphabet_indices = new std::vector<int> (256, -1);
	for (int i = 0; i < self->alphabet_len; i++)
	{
		if (self->alphabet_indices->at(temp_swapcase[i]) != -1)
			self->alphabet_indices->at(temp_alphabet[i]) = self->alphabet_indices->at(temp_swapcase[i]);
		else
			self->alphabet_indices->at(temp_alphabet[i]) = self->alphabet_lower_len++;
	}
	
	// Build the automorphisms that are always present.
	self->automorphisms_always = new std::vector< translator* >;
	
	// Can always do the identity automorphism.
	self->automorphisms_always->push_back(build_translator(temp_alphabet, temp_alphabet, self->alphabet_len));
	
	int item_list_len = PySequence_Length(self->Py_automorphisms_always);
	for (int i = 0; i < item_list_len; i++)
	{
		PyObject* item = PySequence_GetItem(self->Py_automorphisms_always, i);
		if (! string_test(item))
		{
			PyErr_SetString(PyExc_TypeError, "Expected string.");
			return NULL;
		}
		const char* temp = get_string(item);
		Py_DECREF(item);
		
		self->automorphisms_always->push_back(build_translator(temp_alphabet, temp, self->alphabet_len));
	}
	self->automorphisms_always_size = int(self->automorphisms_always->size());
	
	self->automorphisms_missing = new std::vector< translator* >;
	self->automorphisms_missing_indices = new std::vector<int>;
	
	int item_list_len2 = PySequence_Length(self->Py_automorphisms_missing);
	for (int i = 0; i < item_list_len2; i++)
	{
		PyObject* item = PySequence_GetItem(self->Py_automorphisms_missing, i);
		PyObject* subitem = PySequence_GetItem(item, 0);
		PyObject* otheritem = PySequence_GetItem(item, 1);
		Py_DECREF(item);
		
		if (! string_test(subitem))
		{
			PyErr_SetString(PyExc_TypeError, "Expected string.");
			return NULL;
		}
		const char* temp = get_string(subitem);
		Py_DECREF(subitem);
		int index = self->alphabet_indices->at(temp[0]);
		
		if (! string_test(otheritem))
		{
			PyErr_SetString(PyExc_TypeError, "Expected string.");
			return NULL;
		}
		const char* automorphism = get_string(otheritem);
		Py_DECREF(otheritem);
		
		self->automorphisms_missing_indices->push_back(index);
		self->automorphisms_missing->push_back(build_translator(temp_alphabet, automorphism, self->alphabet_len));
	}
	self->automorphisms_missing_size = int(self->automorphisms_missing->size());
	
	Py_INCREF(self->Py_automorphisms_always);
	Py_INCREF(self->Py_automorphisms_missing);
	
	return 0;
}

static PyMemberDef c_automorph_members[] = 
{
	{NULL}  /* Sentinel */
};

static PyObject* c_automorph_before_automorphs(c_automorph* self, PyObject* args)
{
	const char* word;
	const char* next_word;
	int word_len;
	int prefix_temp;
	if (! PyArg_ParseTuple(args, "ssii", &word, &next_word, &word_len, &prefix_temp))
		return NULL;
	
	bool prefix = (prefix_temp != 0);
	
	for (int i = 0; i < self->automorphisms_always_size; i++)
		if (! check_automorph(self->symmetric_generators, self->swapcase, self->automorphisms_always->at(i), word, next_word, word_len))
			Py_RETURN_FALSE;
	
	if (! prefix)
	{
		// Find out which letters are missing.
		std::vector<bool> missing (self->alphabet_lower_len, true);
		for (int i = 0; i < word_len; i++)
			missing[self->alphabet_indices->at(next_word[i])] = false;
		
		for (int i = 0; i < self->automorphisms_missing_size; i++)
			if (missing[self->automorphisms_missing_indices->at(i)])
				if (! check_automorph(self->symmetric_generators, self->swapcase, self->automorphisms_missing->at(i), word, next_word, word_len))
					Py_RETURN_FALSE;
	}
	
	Py_RETURN_TRUE;
}



// We need these for pickling / unpickling which is essential for
// allowing this type to be passed to other processes.
static PyObject* c_automorph___getstate__(c_automorph* self, PyObject* args)
{
	return Py_BuildValue("(issOO)", self->symmetric_generators, (char*) self->alphabet->c_str(), (char*) self->alphabet_swapcase->c_str(), self->Py_automorphisms_always, self->Py_automorphisms_missing);
}

static PyObject* c_automorph___setstate__(c_automorph* self, PyObject* args)
{
	PyObject* new_args = PySequence_GetItem(args, 0);
	c_automorph_init(self, new_args, NULL);
	Py_DECREF(new_args);
	
	return Py_BuildValue("");
}

static PyMethodDef c_automorph_methods[] = {
	{"before_automorphs", (PyCFunction)c_automorph_before_automorphs, METH_VARARGS, "Evaluates the FSM on a string."},
	{"__getstate__", (PyCFunction)c_automorph___getstate__, METH_NOARGS, "For pickling."},
	{"__setstate__", (PyCFunction)c_automorph___setstate__, METH_VARARGS, "For depickling."},
	{NULL}  /* Sentinel */
};

static PyTypeObject c_automorph_Type = {
	PyObject_HEAD_INIT(NULL)
#if PY_MAJOR_VERSION < 3
	0,                         /*ob_size*/
#endif
	"c_automorph.c_automorph",               /*tp_name*/
	sizeof(c_automorph),              /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	(destructor)c_automorph_dealloc,  /*tp_dealloc*/
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
	c_automorph_methods,              /* tp_methods */
	c_automorph_members,              /* tp_members */
	0,                         /* tp_getset */
	0,                         /* tp_base */
	0,                         /* tp_dict */
	0,                         /* tp_descr_get */
	0,                         /* tp_descr_set */
	0,                         /* tp_dictoffset */
	(initproc)c_automorph_init,       /* tp_init */
	0,                         /* tp_alloc */
	c_automorph_new,                  /* tp_new */
};

static PyMethodDef module_methods[] = {
	{NULL}  /* Sentinel */
};

static char c_automorph_core_module_doc[] = "This module contains a C++ implementation of a FSM.";

#if PY_MAJOR_VERSION < 3
	PyMODINIT_FUNC initc_automorph_core(void) 
	{
		if (PyType_Ready(&c_automorph_Type) < 0)
			return;
		
		PyObject* m = Py_InitModule3("c_automorph_core", module_methods, c_automorph_core_module_doc);
		
		if (m == NULL)
			return;
		
		Py_INCREF(&c_automorph_Type);
		PyModule_AddObject(m, "c_automorph", (PyObject *)&c_automorph_Type);
	}
#else
	static PyModuleDef c_automorphmodule = {PyModuleDef_HEAD_INIT, "c_automorph", c_automorph_core_module_doc, -1, NULL, NULL, NULL, NULL, NULL};
	
	PyMODINIT_FUNC PyInit_c_automorph_core(void) 
	{
		c_automorph_Type.tp_new = PyType_GenericNew;
		if (PyType_Ready(&c_automorph_Type) < 0)
			return NULL;
		
		PyObject* m = PyModule_Create(&c_automorphmodule);
		if (m == NULL)
			return NULL;
		
		Py_INCREF(&c_automorph_Type);
		PyModule_AddObject(m, "c_automorph", (PyObject *)&c_automorph_Type);
		return m;
	}
#endif