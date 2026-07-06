#ifndef  _Util_Include_
#define  _Util_Include_

#if defined(_MSC_VER) || defined(__BORLANDC__) || defined(__GNUC__)
  #ifndef  REVERSE_BYTE_ORDER
    #define  REVERSE_BYTE_ORDER
  #endif
#endif

#include <iostream>
#include <iomanip>
#include <stdlib.h>

typedef unsigned char  BYTE;    // BYTE for unsigned char

/////////////////////////////////////////////////

// 双向链表基类及节点类型定义

/////////////////////////////////////////////////

struct node_t {
    node_t  *link;		// to next node of list
    node_t  *prev;		// to previous node
    void    *data;		// pointer to user item

    inline node_t()
    {
        link = prev = NULL; 
        data = NULL;
    }
} ;

class list_t {
public:
    node_t  *list;		// pointer to first node
    node_t  *ptr;		// pointer to current node

    list_t();
   ~list_t();

    int  count();		// nodes in the list
    void top();			// ptr to the first node
    void *item();		// item in current node
    void skip();		// ptr to the next node

    void add_node(void *it);	// add a node at the end
    void insert_node(void *it); // insert a node with item
    void delete_node();         // delete current node

    virtual void OnDeleteNode(void *it);  // delete node
} ;

/////////////////////////////////////////////////

// 字符串应用结构类型

/////////////////////////////////////////////////

typedef char*   pchar;      	// Pointer of char array

class vchar {
public:
    unsigned short   len;   	// Length of buffer 'arr'
    char            *arr;   	// Point to memory buffer

    vchar();
   ~vchar();

    vchar(unsigned short length);    // Init with alloc
    vchar(char *name, char *val);    // Init as Field5

    void allocArr();		// Alloc storage for arr
} ;

class VCharList : public list_t {
public:
    VCharList();
   ~VCharList();

    vchar* first();		// Return item in first node
    vchar* next();		// Return item in next node

    void  OnDeleteNode(void *it);   // Delete item of current node
} ;

/////////////////////////////////////////////////

// 数据库查询结果数据类型

/////////////////////////////////////////////////

// Describing columns

struct ColumnInfo {
    char        name[16];       // Column identifier
    char        type[16];       // Data source-dependent type name
    short       sqlType;        // SQL data type
    char        decimal;        // maximum number of decimal digits
    long        length;         // Length in bytes to transfer
} ;

class ColumnList : public list_t {
public:
    ColumnList();
   ~ColumnList();

    ColumnInfo* first();	// return ColumnList in first node
    ColumnInfo* next();		// return ColumnList in next node

    ColumnInfo* find(char *colName);
} ;

// Results selected

struct RecordData {
    long        length;         // Length in bytes to transfer
    char        *data;          // Column data in memory

    inline RecordData()
    {
        length = 0;  data = NULL;
    }

    inline ~RecordData()
   {
        if(data)  delete data;
        length = 0;  data = NULL;
   }
} ;

class RecordList : public list_t {
public:
    unsigned long    numCols;     // Number of columns in result set
    ColumnInfo      *colInfo;     // Description of columns selected

    RecordList();
   ~RecordList();

    void OnDeleteNode(void *it);  // delete item of current node

    RecordData* first();          // return the first RecordData array
    RecordData* next();           // return the next RecordData array
} ;

/////////////////////////////////////////////////

// 自定义记录字段结构类型

/////////////////////////////////////////////////

struct Field5 {

    char    *field;		// Pointer to the field

    /*  Field buffer structure:
    **
    **    0          38  39 40           n
    **    +----------------+-------------+
    **    |     name    |\0|    value    |
    **    +----------------+-------------+
    **
    **  Field5::name()  return name string (not null)
    **  Field5::ptr()   return value string (not null)
    */

    inline Field5()  {field = 0;}

    /*  Attach field to item of VCharList node
    */
    int init(VCharList *list, char *name);

    int init(VCharList *list);

    inline Field5(VCharList *list, char *name)
    {
        this->init(list, name);
    }

    inline Field5(VCharList *list)
    {
        this->init(list);
    }

    char *name();		// return name string
    char *ptr();		// return value string

    operator char();		// to char
    operator int();		// to int
    operator long();		// to long
    operator float();		// to float
    operator double();		// to double
} ;


//////////////////////////////////////////////////////////

// Prototype declearation for common utilties

// Version:  Release 1.0

// Last modify: 1999-10-28

//////////////////////////////////////////////////////////

/** 获取主机字节序信息: 'M'--高字节在先, 'I'--低字节在先
 */
extern char   getHostByteOrder();

/** 字符串析取实用函数
 */
extern char   *skip_blank(char *str);	    // not null
extern char   *next_segment(pchar& str);
extern char   *next_string(pchar& str);	    // not null

/** 拷贝指定长度的字符串到缓冲区（要求缓冲区长度大于len字节）
 */
extern char*  STRnCPY(char *dst, const char *src, unsigned int len);

/** 字节逆序实用函数
 */
extern void   reverse2(char *p);
extern void   reverse4(char *p);
extern void   reverse8(char *p);
extern void   reverseN(char *p, int csz);

/** 求取图形数据元素的存储尺寸
 */
extern int    sizeof_type(char *dataType);

/** 求取指定文件的长度(字节数)
 */
extern size_t sizeof_file(char *fileName);

/** 分配二维指针(数组)
 */
extern char   **new_char(int rows, int cols);
extern short  **new_short(int rows, int cols);
extern long   **new_long(int rows, int cols);
extern float  **new_float(int rows, int cols);
extern double **new_double(int rows, int cols);

#endif
