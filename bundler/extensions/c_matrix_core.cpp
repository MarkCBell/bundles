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
	#define string_concatinate PyString_Concat
	
#else
	#define int_test PyLong_Check
	#define int_convert PyLong_AsLong
	#define int_deconvert PyLong_FromLong
	
	#define string_convert PyBytes_AsString
	#define string_deconvert PyBytes_FromString
	#define string_concatinate PyBytes_Concat
#endif

#define NONE Py_BuildValue("")

extern PyTypeObject c_matrix_Type;

typedef struct 
{
	PyObject_HEAD
	int dimension;
	int dimension2;
	
	long* matrix;
} c_matrix;

static void c_matrix_dealloc(c_matrix* self)
{
	// self->dimension = 0;
	// self->dimension2 = 0;
	
	delete[] self->matrix;
	
	Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject* c_matrix_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	c_matrix* self = (c_matrix *)type->tp_alloc(type, 0);
	if (self == NULL)
		return NULL;
	
	self->dimension = 0;
	self->dimension2 = 0;
	self->matrix = NULL;
	
	return (PyObject*) self;
}

static int c_matrix_init(c_matrix *self, PyObject *args, PyObject *kwds)
{
	PyObject* temp;
	if (!PyArg_ParseTuple(args, "iO", &(self->dimension), &temp))
		return NULL;
	
	self->dimension2 = self->dimension * self->dimension;
	self->matrix = new long[self->dimension2];
	
	for (int k = 0; k < self->dimension2; k++)
	{
		PyObject* item = PySequence_GetItem(temp, k);
		if (! int_test(item))
		{
			PyErr_SetString(PyExc_TypeError, "Expected sequence of integers.");
			return NULL;
		}
		
		self->matrix[k] = int_convert(item);
		Py_DECREF(item);
	}
	
	return 0;
}

static PyMemberDef c_matrix_members[] = 
{
	{NULL}  /* Sentinel */
};

static PyObject* c_matrix_copy(c_matrix* self)
{
	int dimension = self->dimension;
	
	c_matrix* copy = PyObject_NEW(c_matrix, &c_matrix_Type);
	
	copy->dimension = dimension;
	copy->dimension2 = dimension * dimension;
	copy->matrix = new long[copy->dimension2];
	
	for (int i = 0; i < dimension; i++)
		for (int j = 0; j < dimension; j++)
			copy->matrix[i * dimension + j] = self->matrix[i * dimension + j];
	
	return (PyObject*) copy;
}

static PyObject* c_matrix_multiply(c_matrix* self, c_matrix* other_matrix)
{
	if (self->dimension != other_matrix->dimension)
	{
		PyErr_SetString(PyExc_TypeError, "Cannot multiply matrices of different dimensions.");
		return NULL;
	}
	
	int dimension = self->dimension;
	
	c_matrix* product = PyObject_NEW(c_matrix, &c_matrix_Type);
	
	product->dimension = dimension;
	product->dimension2 = dimension * dimension;
	product->matrix = new long[product->dimension2];
	
	for (int i = 0; i < dimension; i++)
		for (int j = 0; j < dimension; j++)
		{
			long c = 0;
			for (int k = 0; k < dimension; k++)
				c += self->matrix[i * dimension + k] * other_matrix->matrix[k * dimension + j];
			
			product->matrix[i * dimension + j] = c;
		}
	
	return (PyObject*) product;
}

static PyObject* c_matrix_add_diagonal(c_matrix* self, PyObject* args)
{
	long diagonal_change;
	if (!PyArg_ParseTuple(args, "l", &diagonal_change))
		return NULL;
	
	for (int k = 0; k < self->dimension2; k += self->dimension + 1)
		self->matrix[k] += diagonal_change;
	
	return NONE;
}

static PyObject* c_matrix_determinant(c_matrix* self)
{
	int dimension = self->dimension;
	int dimension2 = self->dimension2;
	
	// Build a local copy of self->matrix to mess with.
	long* A = new long[dimension2];
	memcpy(A, self->matrix, sizeof(long) * dimension2);
	
	long* rows = new long[dimension];
	for (int i = 0; i < dimension; i++)
		rows[i] = i * dimension;
	
	for (int i = 0; i < dimension; i++)
	{
		if (A[rows[i] + i] == 0)
		{
			bool switch_made = false;
			for (int j = i+1; j < dimension; j++)
				if (A[rows[j] + i] != 0)
				{
					long temp = rows[j];
					rows[j] = rows[i];
					rows[i] = temp;
					switch_made = true;
					break;
				}
			
			if (switch_made == false)
			{
				delete[] rows;
				delete[] A;
				return int_deconvert(0);  // Determinant is 0.
			}
		}
		
		for (int j = i+1; j < dimension; j++)
			for (int k = i+1; k < dimension; k++)
			{
				A[rows[j] + k] = A[rows[j] + k] * A[rows[i] + i] - A[rows[j] + i] * A[rows[i] + k];
				if (i != 0) A[rows[j] + k] = A[rows[j] + k] / A[rows[i-1] + i-1];  // Division is exact.
			}
	}
	
	long det = A[rows[dimension-1] + dimension-1];
	delete[] rows;
	delete[] A;
	return int_deconvert(det);
}

static PyObject* c_matrix_matrix(c_matrix* self, PyObject* args)
{
	PyObject* M = PyList_New(0);
	for (int k = 0; k < self->dimension2; k++)
	{
		PyObject* item = int_deconvert(self->matrix[k]);
		PyList_Append(M, item);
		Py_DECREF(item);
	}
	
	return M;
}

static PyObject* c_matrix_dimension(c_matrix* self, PyObject* args)
{
	return int_deconvert(self->dimension);
}

static PyObject* c_matrix_str(c_matrix* self, PyObject* args)
{
	PyObject* M = c_matrix_matrix(self, NULL);
	PyObject* S = PyObject_Str(M);
	Py_DECREF(M);
	return S;
}

// We need these for pickling / unpickling which is essential for
// allowing this type to be passed to other processes.
static PyObject* c_matrix___getstate__(c_matrix* self, PyObject* args)
{
	PyObject* M = c_matrix_matrix(self, NULL);
	PyObject* N = Py_BuildValue("(iO)", self->dimension, M);
	Py_DECREF(M);
	
	return N;
}

static PyObject* c_matrix___setstate__(c_matrix* self, PyObject* args)
{
	PyObject* new_args = PySequence_GetItem(args, 0);
	c_matrix_init(self, new_args, NULL);
	Py_DECREF(new_args);
	
	return NONE;
}

static PyMethodDef c_matrix_methods[] = {
	{"add_diagonal", (PyCFunction)c_matrix_add_diagonal, METH_VARARGS, "Adds a constant to all entries on the diagonal."},
	{"matrix", (PyCFunction)c_matrix_matrix, METH_NOARGS, "Returns the matrix as a list."},
	{"copy", (PyCFunction)c_matrix_copy, METH_NOARGS, "Returns a copy of the matrix."},
	{"dimension", (PyCFunction)c_matrix_dimension, METH_NOARGS, "Returns the dimension of the matrix."},
	{"determinant", (PyCFunction)c_matrix_determinant, METH_NOARGS, "Returns the determinant of the matrix."},
	{"__getstate__", (PyCFunction)c_matrix___getstate__, METH_NOARGS, "For pickling."},
	{"__setstate__", (PyCFunction)c_matrix___setstate__, METH_VARARGS, "For depickling."},
	{NULL}  /* Sentinel */
};

PyNumberMethods c_matrix_as_number = {
	0,               /* binaryfunc nb_add;         /* __add__ */
	0,               /* binaryfunc nb_subtract;    /* __sub__ */
	(binaryfunc)c_matrix_multiply, /* binaryfunc nb_multiply;    /* __mul__ */
	0,               /* binaryfunc nb_divide;      /* __div__ */
	0,               /* binaryfunc nb_remainder;   /* __mod__ */
	0,            /* binaryfunc nb_divmod;      /* __divmod__ */
	0,               /* ternaryfunc nb_power;      /* __pow__ */
	0,               /* unaryfunc nb_negative;     /* __neg__ */
	0,               /* unaryfunc nb_positive;     /* __pos__ */
	0,               /* unaryfunc nb_absolute;     /* __abs__ */
	0,           /* inquiry nb_nonzero;        /* __nonzero__ */
	0,            /* unaryfunc nb_invert;       /* __invert__ */
	0,            /* binaryfunc nb_lshift;      /* __lshift__ */
	0,            /* binaryfunc nb_rshift;      /* __rshift__ */
	0,               /* binaryfunc nb_and;         /* __and__ */
	0,               /* binaryfunc nb_xor;         /* __xor__ */
	0,                /* binaryfunc nb_or;          /* __or__ */
	0,            /* coercion nb_coerce;        /* __coerce__ */
	0,               /* unaryfunc nb_int;          /* __int__ */
	0,              /* unaryfunc nb_long;         /* __long__ */
	0,             /* unaryfunc nb_float;        /* __float__ */
	0,               /* unaryfunc nb_oct;          /* __oct__ */
	0,               /* unaryfunc nb_hex;          /* __hex__ */
};

PyTypeObject c_matrix_Type = {
	PyObject_HEAD_INIT(NULL)
#if PY_MAJOR_VERSION < 3
	0,                         /*ob_size*/
#endif
	"bundler.extensions.c_matrix",               /*tp_name*/
	sizeof(c_matrix),              /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	(destructor)c_matrix_dealloc,  /*tp_dealloc*/
	0,                         /*tp_print*/
	0,                         /*tp_getattr*/
	0,                         /*tp_setattr*/
	0,                         /*tp_compare*/
	0,                         /*tp_repr*/
	&c_matrix_as_number,                         /*tp_as_number*/
	0,                         /*tp_as_sequence*/
	0,                         /*tp_as_mapping*/
	0,                         /*tp_hash */
	0,                         /*tp_call*/
	(reprfunc)c_matrix_str,              /*tp_str*/
	0,                         /*tp_getattro*/
	0,                         /*tp_setattro*/
	0,                         /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,  /*tp_flags*/
	"A C++ implementation of a matrix.",          /* tp_doc */
	0,                         /* tp_traverse */
	0,                         /* tp_clear */
	0,                         /* tp_richcompare */
	0,                         /* tp_weaklistoffset */
	0,                         /* tp_iter */
	0,                         /* tp_iternext */
	c_matrix_methods,              /* tp_methods */
	c_matrix_members,              /* tp_members */
	0,                         /* tp_getset */
	0,                         /* tp_base */
	0,                         /* tp_dict */
	0,                         /* tp_descr_get */
	0,                         /* tp_descr_set */
	0,                         /* tp_dictoffset */
	(initproc)c_matrix_init,       /* tp_init */
	0,                         /* tp_alloc */
	c_matrix_new,                  /* tp_new */
};

static PyMethodDef module_methods[] = {
    {NULL}  /* Sentinel */
};

static char c_matrix_core_module_doc[] = "This module contains a C++ implementation of a matrix.";

#if PY_MAJOR_VERSION < 3
	PyMODINIT_FUNC initc_matrix_core(void) 
	{
		if (PyType_Ready(&c_matrix_Type) < 0)
			return;
		
		PyObject* m = Py_InitModule3("c_matrix_core", module_methods, c_matrix_core_module_doc);
		
		if (m == NULL)
			return;
		
		Py_INCREF(&c_matrix_Type);
		PyModule_AddObject(m, "c_matrix", (PyObject *)&c_matrix_Type);
	}
#else
	static PyModuleDef c_matrixmodule = {PyModuleDef_HEAD_INIT, "c_matrix", c_matrix_core_module_doc, -1, NULL, NULL, NULL, NULL, NULL};
	
	PyMODINIT_FUNC PyInit_c_matrix_core(void) 
	{
		c_matrix_Type.tp_new = PyType_GenericNew;
		if (PyType_Ready(&c_matrix_Type) < 0)
			return NULL;
		
		PyObject* m = PyModule_Create(&c_matrixmodule);
		if (m == NULL)
			return NULL;
		
		Py_INCREF(&c_matrix_Type);
		PyModule_AddObject(m, "c_matrix", (PyObject *)&c_matrix_Type);
		return m;
	}
#endif
