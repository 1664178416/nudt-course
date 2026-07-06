#ifndef  _SDE_Include_
#define  _SDE_Include_
#include "utili.h"
#include <stdio.h>
#include <time.h>
#include <string.h>

///////////////////////////////////////////////////////////

// Structure and prototype for spatial application

///////////////////////////////////////////////////////////

// 图层定义描述结构类型

/* 说明：
**    1)坐标系统定义
**      若为大地经纬度坐标系统，则 'coordef' = 800;
**      若为高斯-克吕格平面直角坐标系统，则 'coordef' 为
**      投影的中央子午线经度值（单位：度）。
**    2)格网大小
**      'cellsize' 表示格网大小的数值，以度（或米）为单位;
**      'ratio' 表示格网大小描述的比率，为 n:1 ;
**      实际的格网大小为：
**          'cellsize' / 'ratio' 度   （大地坐标时）  或
**          'cellsize' / 'ratio' 米   （高斯坐标时）
**    3)传输字节序
**	统一采用网络字节序, 即Motorola字节序
**	    Motorola:   高字节在先
**	    Intel:      低字节在先
*/

struct LayerDescription {
    char    lname[12];      // Layer name (<= 10 bytes)
    char    theme[12];	    // Theme name (<= 10 bytes)
    char    shape[8];	    // Shape type of spatial object
    char    byteorder[4];   // Byte order of shape data
    float   coordef;        // Longitude of central meridian

    char    datatype[8];    // Data type of cell (<= 6 bytes)
    float   cellsize;	    // Cell size of grid shape
    short   ratio;          // Ratio of unit for cell size
    short   nodata;         // No data value representation

    short   sublayers;      // Number of sub-layers
    short   reserved;       // Reserved for extension

    inline LayerDescription()
    {
        memset(this, 0, sizeof(LayerDescription));
        sublayers = 1;
    }
};

// 空间数据描述结构类型

struct DataDescription {
    long    ncols;          // dots per line
    long    nrows;          // number of lines
    double  xllcorner;      // x-axis is abscissa
    double  yllcorner;      // y-axis is ordinate
    double  cellsize;       // deg/dot or m/dot
    double  reserved;       // no use for grid 

    LayerDescription  *ld;  // layer description

    int     memory;         // 0 - file, 1 - memory
    int     offset;         // data offset
    char    *data;          // data or file-name

    VCharList   *list;      // value list of fields

    inline DataDescription()
    {
        ld = NULL;  data = NULL;  list = NULL;  reserved = 0;
    }

    ~DataDescription();

    void  normalUnits();        // 统一坐标单位
    void  hostByteOrder();      // 转换到主机字节序

    long  bytesPerLine();       // 每行存储字节数
    long  sizeofSubLayer();     // 每个子层的存储量
    long  sizeofData();         // 整个对象的存储量

    int   allocateData();       // 分配对象数据存储

    void  set_NODATA_value();   // 以 NODATA 填充
    void  reverseByteOrder();   // 将数据单元逆序
} ;

struct DataDescription_ {
    long    ncols;          // dots per line
    long    nrows;          // number of lines
    double  xllcorner;      // x-axis is abscissa
    double  yllcorner;      // y-axis is ordinate
    double  cellsize;       // deg/dot or m/dot
    double  reserved;       // no use for grid
} ;


struct TileDescription
{
    long    s_id;           // identification code 
    char    data[256];      //  path of related data
    int     offset;          //  offset of data in special file

    long    ncols;          // dots per line
    long    nrows;          // number of lines
    double  xllcorner;      // low-left corner (abscissa)
    double  yllcorner;      // low-left corner (ordinate)
    double  xtrcorner;      // top-right corner (abscissa)
    double  ytrcorner;      // top-right corner (ordinate)
} ;

// 自定义属性专有处理结构

struct SelfField
{
    char    strings[256];
    int     iData;
    double  fData;

    inline  SelfField()
    {
        memset(this->strings, 0, 256);
    }
};

// 数据对象列表

class DataList : public list_t {
public:
    LayerDescription  *ld;      // layer description

    DataList();
   ~DataList();

    void add(DataDescription *dds);
    void del();

    void OnDeleteNode(void *it);

    DataDescription*  first();  // do normal units here
    DataDescription*  next();
} ;

/////////////////////////////////////////////////

// Grid Data class for desktop processing

/////////////////////////////////////////////////

class GridData {
    int     native;             // if 'dd' is native
public:
    DataDescription  *dd;       // data description

    char    **data;             // data block array
    short   **data_s;           // as 'short' type
    long    **data_l;           // as 'long' type
    float   **data_f;           // as 'float' type
    double  **data_d;           // as 'double' type

    GridData();
    GridData(DataDescription *dds, int asNative=0);
    GridData(char *dataName);

   ~GridData();

    void  init(DataDescription *dds, int asNative=0);
    void  init(char *dataName);

    void  initMSL(DataDescription *dds, int sublayer);

    void    setDataBit(int col, int row, int val);

    int     getDataInt(int col, int row);
    int     getDataInt(double x, double y);

    double  getDataCell(double x, double y);
    double  getDataCell2(double x, double y);
} ;

/////////////////////////////////////////////////

// Entity-based vector shape data class

/////////////////////////////////////////////////

// 3D point type definition

struct POINT3 {
    double  x;              // Coord of abscissa (横坐标值)
    double  y;              // Coord of ordinate (纵坐标值)
    double  z;              // Elevation or attribute value
} ;

struct Entity {
    long    e_id;           // ID number of entity 
    long    npts;           // point num of entity
    POINT3  pt3[1];         // points of {x, y, z}
} ;


class VectData {
    int     native;         	// if 'dd' is native
public:
    DataDescription   *dd;  	// data description

    double  xllbounds;       	// x-coord of low left bound
    double  yllbounds;       	// y-coord of low left bound
    double  xtrbounds;       	// x-coord of top right bound
    double  ytrbounds;       	// y-coord of top right bound

    long    npoints;        	// total points of vector object
    long    nentities;      	// number of entities
    Entity  **data;		// shape data of entities

    VectData();
    VectData(DataDescription *dds);
    VectData(char *dataName);

   ~VectData();

    void  init(DataDescription *dds);
    void  init(char *dataName);
} ;

/////////////////////////////////////////////////////////////

// Procedures for spatial theme data application

// Version:  Release 1.0

// Last modify: 1999-10-28

/////////////////////////////////////////////////////////////

/** 从空间专题数据文件读取首个空间对象(格网或实体)
 */
extern DataDescription  *getData(char *dataName);

/** 从空间专题数据文件读取所有空间对象(格网或实体)
 */
extern DataList  *getDataList(char *dataName);

/** 将指定的空间对象存贮到空间专题数据文件
 */
extern void  putData(DataDescription& dds, char *dataName);

/** 将指定的空间对象列表存贮到空间专题数据文件
 */
extern void  putDataList(DataList& dataList, char *dataName);

/** 读取空间专题数据文件的专题描述段信息
 */
extern FILE *readThemeFile(char *dataName, LayerDescription& ld);

/*
** 从多个文件访问数据，减抽样、拼接（支持多子层）
*/
extern void  merge_from_file(DataDescription& dds, TileDescription *td, int nTiles, long shrink);

//////////////////////////////////////////////////////////

// 空间范围结构类型

//////////////////////////////////////////////////////////

struct SpatialConfine {
    long    s_id;
    float   coordef;
    double  xll, yll;
    double  xtr, ytr;
} ;

class ConfList : public list_t {
public:
    LayerDescription  *ld;  	// layer description

    ConfList();
   ~ConfList();

    void add(SpatialConfine *cnf);
    void del();

    SpatialConfine*  first();
    SpatialConfine*  next();
} ;

//////////////////////////////////////////////////////////

// Job description structure definition (SDAPI0.9)

//////////////////////////////////////////////////////////

struct JobDescription {
    long        j_id;       	// Indentification code
    short       type;           // Job type ( > 0)
    char        status[2];      // Status: 'r'eady, 'p'roc, 'd'one, 's'uspend
    long        para[4];        // Pre-defined parameters
    char        usrData[40];    // User given parameter
} ;

class JobList : public list_t {
public:
    JobList();
   ~JobList();

    void add(JobDescription *jd);
    void del();

    JobDescription*   first();
    JobDescription*   next();
} ;


//////////////////////////////////////////////////////////////

// Job Definition (SDAPI 1.1)

//////////////////////////////////////////////////////////////

struct JobDefinition
{
    long    	job_no;           // 作业号(>0)
    short     	algo_id;          // 算法标识(>0)
    char        status[2];        // 作业分配状态
    float    	xllcorner;        // 左下角点东向坐标值
    float       yllcorner;        // 左下角点北向坐标值
    float       xtr4query;        // 查询范围的右上角点东向坐标值
    float       ytr4query;        // 查询范围的右上角点北向坐标值
    char     	description[40];  // 注释字符串

    inline JobDefinition()
    {
        memset(this, 0, sizeof(JobDefinition));
        xllcorner = yllcorner = 0.0f;
        xtr4query = ytr4query = 0.0f;
    }
} ;

class JobDefList : public list_t {
public:
    JobDefList();
   ~JobDefList();

    void add(JobDefinition *jd);
    void del();

    JobDefinition*   first();
    JobDefinition*   next();
} ;

/////////////////////////////////////////////////////////////

// Algorithm Module Definition 

/////////////////////////////////////////////////////////////

struct  AlgoRegInfo
{
     short    	algo_id;            // 算法标识(>0)
     char   	platform[10];       // 'windows'、'solaris'、'linux'
     char    	algo_func[16];      // 算法功能助记字符串
     char       prod_date[40];      // 算法最近修改的日期(Last Modification Time)
     char     	algo_path[128];     // 算法可执行程序的路径
     char     	description[256];   // 算法描述信息

     inline AlgoRegInfo()
     {
         memset(this, 0, sizeof(AlgoRegInfo));
     }
};

/////////////////////////////////////////////////////////////

// Procedures for file type convert

// Version:  Release 1.0

// Last modify: 1999-11-09

/////////////////////////////////////////////////////////////

/** 将ARC/INFO ASCII格网数据文件转换为空间专题数据文件
 */
extern void  asciiFileToDataFile(char *fileName, char *theme, float coordef, char *dataType, short ratio, char *dataName);

/** 将格网的空间专题数据文件转换为ARC/INFO ASCII数据文件
 */
extern void  dataFileToAsciiFile(char *dataName, char *fileName);

/** 将格网的空间数据对象输出到ARC/INFO ASCII数据文件
 */
extern int   putDataToAsciiFile(DataDescription& dds, char *fileName);

/** 将专题地图文件(.tmf)转换为空间专题数据文件
 */
extern void  themeFileToDataFile(char *themeName, char *dataName);

/** 将空间专题数据文件转换为专题地图文件(.tmf)
 */
extern void  dataFileToThemeFile(char *dataName, char *themeName);


/** 从文件读取记录列表("属性—值"对)
 */
extern VCharList *readRecordList(char *fileName, int raw=0);


/////////////////////////////////////////////////////////////

// Other utilities for spatial application 

/////////////////////////////////////////////////////////////

/** 读取单个空间对象的属性(若为矢量对象则同时取图形数据)
 */
extern DataDescription  *getDataInfo(char *dataName);

/** 将空间对象的属性信息存储到属性文件
 */
extern void  putData(DataDescription& dds);

/** 读取所有空间对象的属性(若为矢量对象则同时取图形数据)
 */
extern DataList  *getDataListInfo(char *dataName);

/** 对格网列表进行无缝拼接
 */
extern GridData  *getSeamless(DataList *datalist);

/** 求矢量图形对象的覆盖范围
 */
extern int  getShapeBound(DataDescription& dds);



/** 求矢量图形对象列表的覆盖范围
 */
//extern int  confineOfDataList(DataList& dataList, SpatialConfine& scf);

/** 求矢量图形对象覆盖范围的总覆盖范围
 */
//extern int  confineOfConfList(ConfList& confList, SpatialConfine& scf);

#endif
