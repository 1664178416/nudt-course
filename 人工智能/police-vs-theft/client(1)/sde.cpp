#include "stdafx.h"
#include "sde.h"

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#ifdef  _MSC_VER
    #include <direct.h>
    #include <strstream>
#else
    #include <unistd.h> 
    #include <strstream.h>
#endif

#include <fstream>
using namespace std;
/////////////////////////////////////////////////////////////

// 实现空间专题数据文件规范的底层函数

/////////////////////////////////////////////////////////////

/** 打开空间专题数据文件并读取专题描述段信息
 */
extern FILE *readThemeFile(char *dataName, LayerDescription& ld);

/** 移动文件读指针到空间对象描述段的开始处
 */
static int goNextObject(FILE *fp);

/** 从fp读入对象属性以及从fd读入图形数据
 */
static DataDescription *getObject(LayerDescription *ld, FILE *fp, FILE *fd);

/** 输出图层专题描述段信息到指定的文件流
 */
static void putLayerDescription(LayerDescription& ld, ofstream& ofs);

/** 输出对象属性以及图形数据(当fp非空时)
 */
static void putObject(DataDescription& dds, ofstream& ofs, FILE *fp=NULL);

/////////////////////////////////////////////////

// Member functions of struct "DataDescription"

/////////////////////////////////////////////////

DataDescription::~DataDescription()
{
    delete data;  data = NULL;
    delete ld;  ld = NULL;
    delete list;  list = NULL;
}

void DataDescription::normalUnits()
{
    /*
    ** 若不是格网类型，则不作处理
    */
    if(ld->shape[0] != 'g')  return;

    if(ld->ratio <= 1  ||  !reserved)  return;

    double  dratio = (double)ld->ratio;
    xllcorner /= dratio;
    yllcorner /= dratio;
    cellsize  /= dratio;

    reserved = 0;
}

void DataDescription::reverseByteOrder()
{
    /*
    ** 判断图形数据是否在内存中有效
    */
    if( !memory  ||  !data )  return;

    /*
    ** 矢量数据类型
    */
    if(ld->shape[0] != 'g')
    {
        char  *src = data;
        for(int k = 0, npoints = 0; k < nrows; k ++)
        {
            reverse4(src);
            long  e_id = *((long *)src);
            src += 4;
            reverse4(src);
            long  npts = *((long *)src);
            src += 4;
            for(int i = 0; i < npts && npoints < ncols; i ++, npoints ++)
            {
                 POINT3  *pt3 = (POINT3 *)src;
                 src += sizeof(POINT3);
                 reverse8((char *)&pt3->x);
                 reverse8((char *)&pt3->y);
                 reverse8((char *)&pt3->z);
            }
        }
        return;
    }

    /*
    ** 格网数据类型
    */
    int  cz = sizeof_type(ld->datatype);
    if(cz == 1)  return;

    for(int l = 0; l < ld->sublayers; l ++)
    {
        char  *src = data + sizeofSubLayer() * l;

        for(int k = 0, j = 0; j < nrows; j ++)
        for(int i = 0; i < ncols; i ++, k += cz)
        {
            char  *p = src + k;
            reverseN(p, cz);
        }
    }
}

void DataDescription::hostByteOrder()
{
    if( !memory  ||  !data )  return;

    char  bo = getHostByteOrder();

    if(*ld->byteorder == bo)  return;

    this->reverseByteOrder();

    *ld->byteorder = bo;
}

long DataDescription::bytesPerLine()
{
    if(ncols < 1  ||  nrows < 1)  return 0;
    if(ld->shape[0] != 'g')  return 0;

    if(strcmp(ld->datatype, "tbit") == 0)
    {
        int  len = ncols >> 3;
        if(ncols > (len << 3))  len ++;
        return len;
    }

    if(ncols > 10000000)  return 0;

    return (sizeof_type(ld->datatype) * ncols);
}

long DataDescription::sizeofSubLayer()
{
    if(ncols < 1  ||  nrows < 1)  return 0;

    if(ld->shape[0] != 'g')  return 0;

    long  cllen = bytesPerLine();

    long  lz = cllen * nrows;

    // 检查long类型数据是否越界

    long  check = lz / nrows;

    if(check != cllen)  return 0;

    return ( lz );
}

long DataDescription::sizeofData()
{
    if(ld->shape[0] == 'g')
    {
        if(ld->sublayers < 1  ||  ld->sublayers > 1000)  ld->sublayers = 1;

        long LenOfSub = sizeofSubLayer();

        long lz = LenOfSub * ld->sublayers;

        // 检查long类型数据是否越界

        long check = lz / (ld->sublayers);

        if( check != LenOfSub ) return 0;

        return ( lz );
    }
    else
    {
        if(ncols < 1  ||  nrows < 1)  return 0;

        // 防止long类型数据越界

        if(ncols > 1000000  ||  nrows > 100000)  return 0;

	    return (sizeof(POINT3) * ncols + sizeof(long) * 2 * nrows);
    }
}

int DataDescription::allocateData()
{
    if(data)  {delete data; data = NULL;}

    memory = 1;  offset = 0;

    long  szdata = sizeofData();
    if(szdata < 1)  return -1;

    data = new char [szdata];
    if( !data )  return -1;

    return 0;
}

/////////////////////////////////////////////////

// Member functions of class "DataList"

/////////////////////////////////////////////////

DataList::DataList()
{
    ld = NULL;
}

DataList::~DataList()
{
    // Release all spatial data objects

    if(ld)  delete ld;

    ld = NULL;

    while(list)
    {
        ptr = list;
        list = ptr->link;
        OnDeleteNode(ptr->data);
        delete ptr;
    }
}

void DataList::OnDeleteNode(void *it)
{
    if(it)
    {
        DataDescription  *dds = (DataDescription *)it;
        dds->ld = NULL;  delete dds;
    }
}

void DataList::add(DataDescription *dds)
{
    if( !dds )  return;

    if( !ld )  ld = dds->ld;

    if(dds->ld != ld)
    {
        delete dds->ld;
        dds->ld = ld;
    }

    list_t::add_node(dds);
}

void DataList::del()
{
    list_t::delete_node();
}

DataDescription* DataList::first()
{
    top();

    return (DataDescription *)item();
}

DataDescription* DataList::next()
{
    skip();

    return (DataDescription *)item();
}

/////////////////////////////////////////////////

// Member functions of class "ConfList"

/////////////////////////////////////////////////

ConfList::ConfList()
{
    ld = NULL;
}

ConfList::~ConfList()
{
    if(ld)  delete ld;

    ld = NULL;
}

void ConfList::add(SpatialConfine *cnf)
{
    list_t::add_node(cnf);
}

void ConfList::del()
{
    list_t::delete_node();
}

SpatialConfine* ConfList::first()
{
    top();

    return (SpatialConfine *)item();
}

SpatialConfine* ConfList::next()
{
    skip();

    return (SpatialConfine *)item();
}

/////////////////////////////////////////////////

// Member functions of class "JobList"

/////////////////////////////////////////////////

JobList::JobList() {}

JobList::~JobList()
{
    // Release all job info

    for(top(); ptr; skip())
    {
        JobDescription  *q = (JobDescription *)item();
        delete q;
        ptr->data = NULL;
    }
}

void JobList::add(JobDescription *jd)
{
    if( !jd )  return;
    add_node(jd);
}

void JobList::del()
{
    JobDescription  *jd = (JobDescription *)item();
    if(jd)  {delete jd;}

	list_t::delete_node();
}

JobDescription* JobList::first()
{
    top();

    return (JobDescription *)item();
}

JobDescription* JobList::next()
{
    skip();

    return (JobDescription *)item();
}

////////////////////////////////////////////////////////////

//  member functions of JobDefList

////////////////////////////////////////////////////////////
JobDefList::JobDefList() {}

JobDefList::~JobDefList()
{
    // Release all job info

    for(top(); ptr; skip())
    {
        JobDefinition  *q = (JobDefinition *)item();
        delete q;
        ptr->data = NULL;
    }
}

void JobDefList::add(JobDefinition *jd)
{
    if( !jd )  return;
    add_node(jd);
}

void JobDefList::del()
{
    JobDefinition  *jd = (JobDefinition *)item();
    if(jd)  {delete jd;}

	list_t::delete_node();
}

JobDefinition* JobDefList::first()
{
    top();

    return (JobDefinition *)item();
}

JobDefinition* JobDefList::next()
{
    skip();

    return (JobDefinition *)item();
}

///////////////////////////////////////////////////////////

//  Spatial Confine

///////////////////////////////////////////////////////////

int confineOfDataList(DataList& dataList, SpatialConfine& scf)
{
    DataDescription  *dds = dataList.first();
    if( !dds )  return -1;

    scf.s_id = 0;
    scf.coordef = dds->ld->coordef;

    if(dds->ld->shape[0] == 'g')
    {
        double  xll = dds->xllcorner;
        double  yll = dds->yllcorner;
        double  xtr = xll + (dds->ncols - 1) * dds->cellsize;
        double  ytr = yll + (dds->nrows - 1) * dds->cellsize;
        
        scf.xll = xll;  scf.yll = yll;
        scf.xtr = xtr;  scf.ytr = ytr;
        
        for(dds = dataList.next(); dds; dds = dataList.next())
        {
            xll = dds->xllcorner;
            yll = dds->yllcorner;
            xtr = xll + (dds->ncols - 1) * dds->cellsize;
            ytr = yll + (dds->nrows - 1) * dds->cellsize;
            if(xll < scf.xll)  scf.xll = xll;
            if(yll < scf.yll)  scf.yll = yll;
            if(xtr > scf.xtr)  scf.xtr = xtr;
            if(ytr > scf.ytr)  scf.ytr = ytr;
        }
    }
    else
    {
        double  xll = dds->xllcorner;
        double  yll = dds->yllcorner;
        double  xtr = dds->cellsize;
        double  ytr = dds->reserved;
        
        scf.xll = xll;  scf.yll = yll;
        scf.xtr = xtr;  scf.ytr = ytr;
        
        for(dds = dataList.next(); dds; dds = dataList.next())
        {
            xll = dds->xllcorner;
            yll = dds->yllcorner;
            xtr = dds->cellsize;
            ytr = dds->reserved;
            if(xll < scf.xll)  scf.xll = xll;
            if(yll < scf.yll)  scf.yll = yll;
            if(xtr > scf.xtr)  scf.xtr = xtr;
            if(ytr > scf.ytr)  scf.ytr = ytr;
        }
    }

    return  0;
}

int confineOfConfList(ConfList& confList, SpatialConfine& scf)
{
    SpatialConfine  *cfn = confList.first();
    if( !cfn )  return -1;

    scf.s_id = 0;
    scf.coordef = cfn->coordef;
    scf.xll = cfn->xll;
    scf.yll = cfn->yll;
    scf.xtr = cfn->xtr;
    scf.ytr = cfn->ytr;

    for(cfn = confList.next(); cfn; cfn = confList.next())
    {
        if(cfn->xll < scf.xll)  scf.xll = cfn->xll;
        if(cfn->yll < scf.yll)  scf.yll = cfn->yll;
        if(cfn->xtr > scf.xtr)  scf.xtr = cfn->xtr;
        if(cfn->ytr > scf.ytr)  scf.ytr = cfn->ytr;
    }

    return  0;
}

/////////////////////////////////////////////////////////////

// Read record list from file stream

/////////////////////////////////////////////////////////////

/*
** 从文件流中读取一个有效记录行
*/
static int readOneRecordLine(FILE *fp, char *buff, int len, int raw=0)
{
    /*
    ** 检查记录缓冲区的长度
    */
    if(len < 2)  return -1;
    len -= 2;

    /*
    ** 读入第一个可显示字符（跳过空白符及空行）
    */
    while(1)
    {
        if(fread(buff, 1, 1, fp) < 1)  return -1;
        
        if(buff[0] == '/')      // 过滤注释行
        {
            char  skip;
            while(1)
            {
                 if(fread(&skip, 1, 1, fp) < 1)  break;
                 if(skip == '\n')  break;
            }
            continue;
        }

        if((unsigned)buff[0] > ' ')  break;
    }
    /*
    ** 在读取正常记录行时，检查是否遇到数字行或<object>标识行
    */
    if( !raw  &&  (unsigned)buff[0] < 'A' )
    {
        fseek(fp, -1, SEEK_CUR);  return 1;
    }

    /*
    ** 记录文件读指针的当前位置
    */
    int  pos = ftell(fp);
    /*
    ** 根据余下的缓冲区的长度读入字符串
    */
    int  iRead = fread(buff+1, 1, len, fp);
    if(iRead < 0)  iRead = 0;
    /*
    ** 置字符串结束标记'\0'
    */
    buff[1 + iRead] = '\0';

    /*
    ** 搜索行结束符，提取行记录字符串
    */
    int  j;
    for(j = 1; j <= iRead; j ++)
    {
        if(buff[j] == '\n')  {buff[j] = '\0';  break;}
    }

    /*
    ** 调整文件读指针的位置
    */
    if(j > iRead)
    {
        char  skip;
        /*
        ** 跳过当前记录行剩余的字符串
        */
        while(1)
        {
             if(fread(&skip, 1, 1, fp) < 1)  break;
             if(skip == '\n')  break;
        }
    }
    else
    {
        /*
        ** 移动文件读指针到当前记录行之后
        */
        fseek(fp, pos + j, SEEK_SET);
    }

    return  0;
}

/*
** 从文件流读取记录列表("属性—值"对)，在数据行及<object>标识行前停止
*/
static VCharList *readRecordList(FILE *fp, int raw=0)
{
    if( !fp )  return  NULL;

    char  buffer[256];
    int   nRec = 0;

    VCharList  *recList = new VCharList();
    while(1)
    {
        int  rc = readOneRecordLine(fp, buffer, 256);
        if(rc != 0)  break;
        char  *str = buffer;
        vchar  *rec = new vchar();
        rec->len = 100;
        rec->arr = new char [rec->len];
        strncpy(rec->arr, next_string(str), 39);
        rec->arr[39] = '\0';
	if(raw)
	{
	    str = skip_blank(str);
            char  *p, *q;
	    for(p = str, q = NULL; *p; p ++)
    	    {
		if((unsigned)*p > ' ')  q = NULL;
		else if( !q )  q = p;
	    }
	    if(q)  *q = '\0';
            strncpy(rec->arr+40, str, 59);
	}
	else
        {
            strncpy(rec->arr+40, next_string(str), 59);
        }
        rec->arr[99] = '\0';
        recList->add_node(rec);
        nRec ++;
    }

    if(nRec == 0)  {delete recList;  recList = NULL;}

    return  recList;
}

VCharList *readRecordList(char *fileName, int raw)
{
    FILE  *fp = fopen(fileName, "rb");
    if( !fp )  return NULL;

    VCharList  *result = readRecordList(fp, raw);

    fclose(fp);
    return result;
}

///////////////////////////////////////////////////////////

// Spatial theme data file input utilities

///////////////////////////////////////////////////////////

FILE *readThemeFile(char *dataName, LayerDescription& ld)
{
    if( !dataName )  return  NULL;

    /*
    ** 构造专题图层属性文件名(加后缀'.rec')
    */
    char  buffer[260];  buffer[259] = '\0';
    ostrstream  oss(buffer, 259);
    oss << dataName << ".rec" << ends;

    /*
    ** 打开专题图层属性文件
    */
    FILE  *fp = fopen(buffer, "rb");
    if( !fp )  return  NULL;
    /*
    ** 读入专题描述段记录列表
    */
    VCharList  *recList = readRecordList(fp);
    if( !recList )
    {
        fclose(fp);  return  NULL;
    }

    int  invalid = 0;
    /*
    ** 将专题图层名设为"noname"
    */
    strncpy(ld.lname, "noname", 10);
    /*
    ** 专题名称
    */
    Field5  field(recList, "THEME");
    strncpy(ld.theme, field.ptr(), 10);
    ld.theme[10] = '\0';
    recList->delete_node();
    /*
    ** 图形类型
    */
    invalid |= field.init(recList, "SHAPE");
    strncpy(ld.shape, field.ptr(), 6);
    ld.shape[6] = '\0';
    recList->delete_node();
    /*
    ** 图形数据字节序
    */
    invalid |= field.init(recList, "BYTEORDER");
    if((char)field == 'I'  ||  (char)field == 'i')
        ld.byteorder[0] = 'I';
    else
        ld.byteorder[0] = 'M';
    ld.byteorder[1] = '\0';
    recList->delete_node();
    /*
    ** 坐标系统定义
    */
    invalid |= field.init(recList, "COORDEF");
    ld.coordef = (float)field;
    recList->delete_node();

    /*
    ** 若为格网类型，则...
    */
    if(ld.shape[0] == 'g')
    {
        /*
        ** 单元数据类型
        */
        invalid |= field.init(recList, "DATATYPE");
        strncpy(ld.datatype, field.ptr(), 7);
        ld.datatype[7] = '\0';
        recList->delete_node();
        /*
        ** 像元尺寸(即格网大小)
        */
        invalid |= field.init(recList, "CELLSIZE");
        ld.cellsize = (float)field;
        if(ld.cellsize <= 0) invalid = -1;
        recList->delete_node();
        /*
        ** 像元尺寸以及角点坐标单位的比率
        */
        field.init(recList, "RATIO");
        ld.ratio = (int)field;
        if(ld.ratio < 1) ld.ratio = 1;
        recList->delete_node();
        /*
        ** 无数据单元的表示值
        */
        field.init(recList, "NODATA");
        ld.nodata = (int)field;
        recList->delete_node();
        /*
        ** 专题图层包含的子层数
        */
        field.init(recList, "SUBLAYERS");
        ld.sublayers = (int)field;
        if(ld.sublayers < 1  ||  ld.sublayers > 1000)  ld.sublayers = 1;
    }
    delete recList;

    /*
    ** 若专题描述段记录信息无效，则返回空的文件指针
    */
    if(invalid)
    {
        fclose(fp);  return NULL;
    }

    return fp;
}

static int goNextObject(FILE *fp)
{
    char  buffer[128];

    if( !fp )  return  -1;

    /*
    ** 搜索并跳过"<object>"标识行
    */
    while(1)
    {
        if(fread(buffer, 1, 1, fp) < 1)  return -1;
        if(*buffer == '<')  break;
    }
    fgets(buffer, 128, fp);

    return  0;
}

static DataDescription *getObject(LayerDescription *ld, FILE *fp, FILE *fd)
{
    if( !ld  ||  !fp  ||  !fd)  return  NULL;

    /*
    ** 读取对象的属性信息列表
    */
    VCharList  *recList = readRecordList(fp);
    if( !recList )  return  NULL;

    /*
    ** 分配DataDescription存储
    */
    DataDescription  *result = new DataDescription();
    result->ld = ld;
    result->list = recList;

    int  invalid = 0;
    /*
    ** 获得数据存储位置偏移量，并移动数据文件指针
    */
    Field5  field(recList, "DATAOFF");
    result->offset = (int)field;
    recList->delete_node();
    if(result->offset < 0)  invalid = -1;
    if(fseek(fd, result->offset, SEEK_SET) < 0)  invalid = -1;

    /*
    ** 处理格网数据对象的公共属性
    */
    if(*result->ld->shape == 'g')
    {
        invalid |= field.init(recList, "NCOLS");
        result->ncols = (int)field;
        recList->delete_node();
        invalid |= field.init(recList, "NROWS");
        result->nrows = (int)field;
        recList->delete_node();
		invalid |= field.init(recList, "XLLCORNER");
        result->xllcorner = (double)field;
        recList->delete_node();
		invalid |= field.init(recList, "YLLCORNER");
        result->yllcorner = (double)field;
        recList->delete_node();

        result->cellsize = ld->cellsize;
        result->reserved = 0;

        if(ld->ratio > 1)  result->reserved = 1;
    }
    else
    {
        invalid |= field.init(recList, "NPOINTS");
        result->ncols = (int)field;
        recList->delete_node();
        invalid |= field.init(recList, "NENTITIES");
        result->nrows = (int)field;
        recList->delete_node();
    }
    if(result->ncols < 1  ||  result->nrows < 1)  invalid = -1;

    if(invalid)
    {
        result->ld = NULL;  delete result;  return NULL;
    }

    /*
    ** 计算数据的存储空间大小，分配内存
    */
    unsigned long  dataSize = result->sizeofData();
    result->allocateData();
    if( !result->data )
    {
        result->ld = NULL;  delete result;  return NULL;
    }

    /*
    ** 读取空间数据数据
    */
    if(fread(result->data, 1, dataSize, fd) != dataSize)
    {
        result->ld = NULL;  
		delete result;  
		return NULL;
    }

    /*
    ** 调整数据的字节序
    */
    result->hostByteOrder();

    /*
    ** 获取矢量图形的空间范围
    */
    if(*ld->shape != 'g') if(getShapeBound(*result) != 0)
    {
        result->ld = NULL;  delete result;  return  NULL;
    }

    return result;
}

int getShapeBound(DataDescription& dds)
{
    if(dds.ld->shape[0] == 'g')  return -1;

    char  *src = dds.data;
    if( !src )  return -1;

    dds.hostByteOrder();

    double  xll, yll, xtr, ytr;
    int  first = 1;
    int  nentities, npoints;
    for(nentities = 0, npoints = 0; nentities < dds.nrows; nentities ++)
    {
        long  npts = *((long *)(src+4));
		src += 8;
        for(int i = 0; i < npts && npoints < dds.ncols; i ++, npoints ++)
        {
            POINT3  *pt3 = (POINT3 *)src;
            src += sizeof(POINT3);

            if(dds.ld->shape[0] != 'a')          // 'point' or 'line'
            {
                if(first)
                {
                    first = 0;
                    xll = xtr = pt3->x; 
                    yll = ytr = pt3->y;
                    continue;
                }

                if(pt3->x < xll)  xll = pt3->x;
                if(pt3->y < yll)  yll = pt3->y;
                if(pt3->x > xtr)  xtr = pt3->x;
                if(pt3->y > ytr)  ytr = pt3->y;
            }
            else
            {
                if(npts == 1)    	    // 'circle'
                {
                    double  sd_xll = pt3->x - pt3->z;
                    double  sd_yll = pt3->y - pt3->z;
                    double  sd_xtr = pt3->x + pt3->z;
                    double  sd_ytr = pt3->y + pt3->z;
                    if(first)
                    {
                        first = 0;
                        xll = sd_xll;  yll = sd_yll;
                        xtr = sd_xtr;  ytr = sd_ytr;
                    }
                    else
                    {
                        if(sd_xll < xll)  xll = sd_xll;
                        if(sd_yll < yll)  yll = sd_yll;
                        if(sd_xtr > xtr)  xtr = sd_xtr;
                        if(sd_ytr > ytr)  ytr = sd_ytr;
                    }
                    continue;
                }

		// 'rectangle' or 'region'

                if(first)
                {
                    first = 0;
                    xll = xtr = pt3->x; 
                    yll = ytr = pt3->y;
                    continue;
                }

                if(pt3->x < xll)  xll = pt3->x;
                if(pt3->y < yll)  yll = pt3->y;
                if(pt3->x > xtr)  xtr = pt3->x;
                if(pt3->y > ytr)  ytr = pt3->y;
            }
        }
    }
    dds.xllcorner = xll;  dds.cellsize = xtr;
    dds.yllcorner = yll;  dds.reserved = ytr;

    if(nentities != dds.nrows  ||  npoints != dds.ncols)  return -1;
    
    return 0;
}

/*
** 接口函数(SDAPI-1)
**
** 功能：从内部数据文件读入空间专题数据
**
** 输入：char *dataName  --  空间专题数据名，长度不超过255字节（包括后缀），后缀".rec"可以省略。
**
** 返回：当成功时，返回的指针指向DataDescription结构。
**
** 最后修改的时间：2002年1月22日
*/
DataDescription *getData(char *dataName)
{
    char  stdDataName[256];             // 用于提取空间专题数据名

    /*
    ** 若文件名包含了后缀".rec"，则自动去除后缀
    */
    if( !dataName )  return NULL;
    char  *ext = strrchr(dataName, '.');
    if(ext) if(strcmp(ext + 1, "rec") == 0)
    {
        int  len = ext - dataName;
        if(len > 255)  return NULL;
        strncpy(stdDataName, dataName, len);
        stdDataName[len] = '\0';
        dataName = stdDataName;
    }

    /*
    ** 打开数据文件
    */
    FILE  *fd = fopen(dataName, "rb");
    if( !fd )  return NULL;

    /*
    ** 打开专题属性描述文件
    */
    LayerDescription  *ld = new LayerDescription();
    FILE  *fp = readThemeFile(dataName, *ld);
    if( !fp  ||  ld->shape[0] == 't' )
    {
        fclose(fd);  delete ld;  return NULL;
    }

    goNextObject(fp);
    DataDescription  *result = getObject(ld, fp, fd);
    if( !result )  delete ld;

    fclose(fp);
    fclose(fd);

    return  result;
}

DataList *getDataList(char *dataName)
{
    FILE  *fd = fopen(dataName, "rb");
    if( !fd )  return NULL;

    LayerDescription  *ld = new LayerDescription();
    FILE  *fp = readThemeFile(dataName, *ld);
    if( !fp  ||  ld->shape[0] == 't' )
    {
        fclose(fd);  delete ld;  return NULL;
    }

    DataList  *dataList = new DataList();
    dataList->ld = ld;
    char  bo = ld->byteorder[0];

    while(1)
    {
        if(goNextObject(fp) == -1)  break;
        ld->byteorder[0] = bo;
        DataDescription  *dd = getObject(ld, fp, fd);
        if( !dd )  break;
        dataList->add(dd);
    }

    fclose(fd);
    fclose(fp);

    return  dataList;
}

DataDescription *getDataInfo(char *dataName)
{
    if( !dataName )  return NULL;

    LayerDescription  *ld = new LayerDescription();
    FILE  *fp = readThemeFile(dataName, *ld);
    if( !fp )
    {
        delete ld;  return NULL;
    }

    // If object shape is not grid type ...

    if(ld->shape[0] != 'g')
    {
	fclose(fp);  delete ld;
	return getData(dataName);
    }

    goNextObject(fp);

    VCharList  *recList = readRecordList(fp);
    fclose(fp);

    if( !recList )  {delete ld;  return NULL;}

    DataDescription  *result = new DataDescription();
    result->ld = ld;
    result->list = recList;

    Field5  field(recList, "DATAOFF");
    result->offset = (int)field;
    recList->delete_node();

    int  invalid = 0;

    invalid |= field.init(recList, "NCOLS");
    result->ncols = (int)field;
    recList->delete_node();
    invalid |= field.init(recList, "NROWS");
    result->nrows = (int)field;
    recList->delete_node();
    invalid |= field.init(recList, "XLLCORNER");
    result->xllcorner = (double)field;
    recList->delete_node();
    invalid |= field.init(recList, "YLLCORNER");
    result->yllcorner = (double)field;
    recList->delete_node();

    result->cellsize = ld->cellsize;

    if(ld->ratio < 1)  invalid |= -1;
    if(ld->ratio > 1)  result->reserved = 1;

    if(result->offset < 0)  invalid = -1;
    if(result->ncols < 1  ||  result->nrows < 1)  invalid = -1;

    if(invalid != 0)
    {
        delete result;  return NULL;
    }

    result->memory = 0;
    result->data = strdup(dataName);

    return result;
}

DataList *getDataListInfo(char *dataName)
{
    if( !dataName )  return NULL;

    LayerDescription  *ld = new LayerDescription;
    FILE  *fp = readThemeFile(dataName, *ld);
    if( !fp )
    {
        delete ld;  return NULL;
    }

    // If object shape is not grid type ...

    if(ld->shape[0] != 'g')
    {
	fclose(fp);  delete ld;
	return getDataList(dataName);
    }

    DataList  *dataList = new DataList();
    dataList->ld = ld;
    while(1)
    {
        if(goNextObject(fp) == -1)  break;
	VCharList  *recList = readRecordList(fp);

        if( !recList )  break;

        DataDescription  *result = new DataDescription();
        result->list = recList;

        Field5  field(recList, "DATAOFF");
        result->offset = (int)field;
        recList->delete_node();

        int  invalid = 0;

        invalid |= field.init(recList, "NCOLS");
        result->ncols = (int)field;
        recList->delete_node();
        invalid |= field.init(recList, "NROWS");
        result->nrows = (int)field;
        recList->delete_node();
        invalid |= field.init(recList, "XLLCORNER");
        result->xllcorner = (double)field;
        recList->delete_node();
        invalid |= field.init(recList, "YLLCORNER");
        result->yllcorner = (double)field;
        recList->delete_node();

        result->cellsize = ld->cellsize;

        if(ld->ratio < 1)  invalid |= -1;
        if(ld->ratio > 1)  result->reserved = 1;

        if(result->offset < 0)  invalid = -1;
        if(result->ncols < 1  ||  result->nrows < 1)  invalid = -1;

        if(invalid != 0)
        {
            delete result;  break;
        }

        result->ld = ld;
        result->memory = 0;
        result->data = strdup(dataName);
        dataList->add(result);
    }

    fclose(fp);

    return dataList;
}

/////////////////////////////////////////////////

// Report record name and value utilities

/////////////////////////////////////////////////

static void report_name(ofstream& ofs, char *name)
{
    int  len = 0;
    if(name)  len = strlen(name);
    if(len == 0)
    {
        ofs << "NO_NAME         ";
        return;
    }

    if(len > 15)
        ofs << setw(15) << name << " ";
    else
    {
        ofs << name;
        for( ;len < 16; len ++) ofs << " ";
    }
}

void report_value(ofstream& ofs, char *name, char *value)
{
    if( !value )  return;

    report_name(ofs, name);
    ofs << value << endl;
}

void report_value(ofstream& ofs, char *name, long value)
{
    report_name(ofs, name);
    ofs << value << endl;
}

void report_value(ofstream& ofs, char *name, int value)
{
    report_name(ofs, name);
    ofs << value << endl;
}

void report_value(ofstream& ofs, char *name, short value)
{
    report_name(ofs, name);
    ofs << value << endl;
}

void report_value(ofstream& ofs, char *name, double value)
{
    report_name(ofs, name);
    ofs.setf(ios::fixed, ios::floatfield);
    ofs << setprecision(16) << value << endl;
}

void report_value(ofstream& ofs, char *name, float value)
{
    report_name(ofs, name);
    ofs.setf(ios::fixed, ios::floatfield);
    ofs << setprecision(8) << value << endl;
}

///////////////////////////////////////////////////////////

// Spatial theme data file output utilities

// EXTERN
//   putDataList()   -- 输出所有对象到空间专题数据文件
//   putData()       -- 输出对象(调用putObject()实现)

///////////////////////////////////////////////////////////

static void putLayerDescription(LayerDescription& ld, ofstream& ofs)
{
    report_value(ofs, "THEME", ld.theme);
    report_value(ofs, "SHAPE", ld.shape);
    if(*ld.byteorder == 'I' || *ld.byteorder == 'i')
        report_value(ofs, "BYTEORDER", "Intel");
    else
        report_value(ofs, "BYTEORDER", "Motorola");
    report_value(ofs, "COORDEF", ld.coordef);

    if(ld.shape[0] == 'g')
    {
        report_value(ofs, "DATATYPE", ld.datatype);
        report_value(ofs, "CELLSIZE", ld.cellsize);
        report_value(ofs, "RATIO", ld.ratio);
        report_value(ofs, "NODATA", ld.nodata);
        if(ld.sublayers > 1  &&  ld.sublayers <= 1000)
        {
            report_value(ofs, "SUBLAYERS", ld.sublayers);
        }
    }
}

static void putObject(DataDescription& dds, ofstream& ofs, FILE *fp)
{
    ofs << endl << "<OBJECT>" << endl << endl;

    if(*dds.ld->shape == 'g')
    {
        report_value(ofs, "NCOLS", dds.ncols);
        report_value(ofs, "NROWS", dds.nrows);
	if(dds.ld->ratio > 1  &&  !dds.reserved)
	{
            report_value(ofs, "XLLCORNER", dds.xllcorner*(double)dds.ld->ratio);
            report_value(ofs, "YLLCORNER", dds.yllcorner*(double)dds.ld->ratio);
	}
	else
	{
            report_value(ofs, "XLLCORNER", dds.xllcorner);
            report_value(ofs, "YLLCORNER", dds.yllcorner);
	}
    }
    else
    {
        report_value(ofs, "NPOINTS", dds.ncols);
        report_value(ofs, "NENTITIES", dds.nrows);
    }

    if(fp == NULL)      // 无需写图形数据文件
    {
        report_value(ofs, "DATAOFF", dds.offset);
    }
    else
    {
        size_t  dataSize = dds.sizeofData();

        int  pos = ftell(fp);
        if( !dds.data )  return;

        if(dds.memory)
            fwrite(dds.data, dataSize, 1, fp);
        else
        {
            FILE  *ft = fopen(dds.data, "rb");
            if(ft)
            {
                char  buffer[1024];
                fseek(ft, dds.offset, SEEK_SET);
                for(int cnt = dataSize; cnt > 0; )
                {
                    int  nBytes = cnt > 1024 ? 1024 : cnt;
                    fread(buffer, nBytes, 1, ft);
                    fwrite(buffer, nBytes, 1, fp);
                    cnt -= nBytes;
                }
                fclose(ft);
            }
        }
        report_value(ofs, "DATAOFF", pos);
    }

    ofs << endl;

    VCharList  *p = dds.list;
    if(p) for(vchar *rec = p->first(); rec; rec = p->next())
    {
        char  *name = rec->arr;
        char  *value = skip_blank(rec->arr + 40);
        report_value(ofs, name, value);
    }
}

void putDataList(DataList& dataList, char *dataName)
{
    LayerDescription  *ld = dataList.ld;
    if( !ld )  return;

    if( !dataName )  return;
    char  reportFile[128];  reportFile[127] = '\0';
    ostrstream  oss(reportFile, 127);
    oss << dataName << ".rec" << ends;
    ofstream  ofs(reportFile);
    if( !ofs )  return;

    FILE  *fp = NULL;
    fp = fopen(dataName, "wb");
    if( !fp )  {ofs.close();  return;}

    // Report layer description

    putLayerDescription(*ld, ofs);

    // Report all data object

    DataDescription  *dds = dataList.first();
    while(dds)
    {
        putObject(*dds, ofs, fp);
        dds = dataList.next();
    }

    fclose(fp);
    ofs.close();
}

void putData(DataDescription& dds, char *dataName)
{
    if( !dataName )  return;
    char  reportFile[128];  reportFile[127] = '\0';
    ostrstream  oss(reportFile, 127);
    oss << dataName << ".rec" << ends;
    ofstream  ofs(reportFile);
    if( !ofs )  return;

    FILE  *fp = NULL;
    fp = fopen(dataName, "wb");
    if( !fp )  {ofs.close();  return;}

    // Report layer description

    putLayerDescription(*dds.ld, ofs);

    // Report data object

    putObject(dds, ofs, fp);

    fclose(fp);
    ofs.close();
}

void putData(DataDescription& dds)
{
    if(dds.memory)  return;
    char  buffer[128];  buffer[127] = '\0';
    ostrstream  oss(buffer, 127);
    oss << dds.data << ".rec" << ends;
    ofstream  ofs(buffer);
    if( !ofs )  return;

    putLayerDescription(*dds.ld, ofs);

    putObject(dds, ofs);

    ofs.close();
}

////////////////////////////////////////////////////

// ARC/INFO的ASCII格网文件  <-->  空间专题数据文件

// STATIC
//   readDataFromFile() -- 从ASCII文件流中读取图形数据

////////////////////////////////////////////////////

static int readDataFromFile(FILE *fi, DataDescription& dds, FILE *fp=NULL)
{
    // Input data is in ascii format

    if(dds.ncols < 1  ||  dds.nrows < 1)  return -1;

    if(fp == NULL)
    {
        dds.ld->byteorder[0] = getHostByteOrder();
        dds.allocateData();
        if( !dds.data )  return -1;
    }
    else  dds.offset = ftell(fp);

    char *dest = dds.data;
    int  ncols = dds.ncols;
    int  nrows = dds.nrows;

    if(dds.ld->shape[0] == 'g') switch(*dds.ld->datatype)
    {
    case    'b':
        {
            BYTE  *data = new BYTE [ncols];
            int  val;
            for(int j = 0; j < nrows; j ++)
            {
                for(int i = 0; i < ncols; i ++)
                {
                    fscanf(fi, "%d", &val);
                    data[i] = (BYTE)val;
                }
                if(fp)
		{
                    fwrite((char *)data, 1, ncols, fp);
		    cout << '\r' << j+1 << " of " << nrows << flush;
		}
                else
                {
                    memcpy(dest, (char *)data, ncols);
                    dest += ncols;
                }
            }
            delete  data;
        }
        break;
    case    's':
        {
            short  *data = new short [ncols];
            int  val;
            for(int j = 0; j < nrows; j ++)
            {
                for(int i = 0; i < ncols; i ++)
                {
                    fscanf(fi, "%d", &val);
                    data[i] = (short)val;
                }
                if(fp)
		{
                    fwrite((char *)data, 2, ncols, fp);
		    cout << '\r' << j+1 << " of " << nrows << flush;
		}
                else
                {
                    memcpy(dest, (char *)data, ncols*2);
                    dest += ncols*2;
                }
            }
            delete  data;
        }
        break;
    case    'i':
    case    'l':
        {
            long  *data = new long [ncols];
            for(int j = 0; j < nrows; j ++)
            {
                for(int i = 0; i < ncols; i ++)
                {
                    fscanf(fi, "%d", &data[i]);
                }
                if(fp)
		{
                    fwrite((char *)data, 4, ncols, fp);
		    cout << '\r' << j+1 << " of " << nrows << flush;
		}
                else
                {
                    memcpy(dest, (char *)data, ncols*4);
                    dest += ncols*4;
                }
            }
            delete  data;
        }
        break;
    case    'f':
        {
            float  *data = new float [ncols];
            for(int j = 0; j < nrows; j ++)
            {
                for(int i = 0; i < ncols; i ++)
                {
                    fscanf(fi, "%f", &data[i]);
                }
                if(fp)
		{
                    fwrite((char *)data, 4, ncols, fp);
		    cout << '\r' << j+1 << " of " << nrows << flush;
		}
                else
                {
                    memcpy(dest, (char *)data, ncols*4);
                    dest += ncols*4;
                }
            }
            delete  data;
        }
        break;
    case    'd':
        {
            double  *data = new double [ncols];
            for(int j = 0; j < nrows; j ++)
            {
                for(int i = 0; i < ncols; i ++)
                {
                    fscanf(fi, "%lf", &data[i]);
                }
                if(fp)
		{
                    fwrite((char *)data, 8, ncols, fp);
		    cout << '\r' << j+1 << " of " << nrows << flush;
		}
                else
                {
                    memcpy(dest, (char *)data, ncols*8);
                    dest += ncols*8;
                }
            }
            delete  data;
        }
        break;
    }
    else for(int k = 0, npoints = 0; k < dds.nrows; k ++)
    {
        char  buffer[256];  buffer[255] = '\0';

        /*
        ** 每个实体的标识号及特征点个数
        */
        fgets(buffer, 255, fi);
        char  *str = buffer;
	long  e_id = atoi(next_string(str));
        long  npts = atoi(next_string(str));
	if(npts <= 0)  {npts = e_id; e_id = 0;}

        if(fp)
        {
	    fwrite((char *)&e_id, 4, 1, fp);
	    fwrite((char *)&npts, 4, 1, fp);
	}
        else
        {
	    memcpy(dest, &e_id, 4); dest += 4;
	    memcpy(dest, &npts, 4); dest += 4;
	}

        /*
        ** 实体的特征点坐标值
        */
        for(int i = 0; i < npts  &&  npoints < dds.ncols; i ++, npoints ++)
        {
            fgets(buffer, 255, fi);
            str = buffer;
            POINT3  pt3;
            pt3.x = atof(next_string(str));
            pt3.y = atof(next_string(str));
            pt3.z = atof(next_string(str));
            if(fp)
                fwrite((char *)&pt3, sizeof(POINT3), 1, fp);
            else
            {
                memcpy(dest, (char *)&pt3, sizeof(POINT3));
                dest += sizeof(POINT3);
            }
        }
    }

    return 0;
}

void asciiFileToDataFile(char *fileName, char *theme, float coordef, char *dataType, short ratio, char *dataName)
{
    if( !fileName  ||  !dataName  ||  !dataType  ||  ratio < 1)  return;
    if( !theme )  theme = "unknown";

    FILE  *fi = fopen(fileName, "rb");
    if( !fi )  {perror(fileName);  return;}

    FILE  *fp = fopen(dataName, "wb");
    if( !fp )  {perror(dataName); fclose(fi);  return;}

    VCharList  *recList = readRecordList(fi);
    if( !recList )
    {
	cout << fileName << ": No record" << endl;
        fclose(fi);  fclose(fp);  return;
    }

    // Match information of data object

    DataDescription  dds;
    dds.ld = new LayerDescription();

    Field5  field;
    int  invalid = 0;

    invalid |= field.init(recList, "ncols");
    dds.ncols = (int)field;
    if(dds.ncols < 1)  invalid = -1;
    invalid |= field.init(recList, "nrows");
    dds.nrows = (int)field;
    if(dds.nrows < 1)  invalid = -1;
    if(field.init(recList, "xllcorner"))
	{
		invalid |= field.init(recList, "XLLCENTER");
	}
    dds.xllcorner = (double)field;
    if(field.init(recList, "yllcorner"))
	{
		invalid |= field.init(recList, "YLLCENTER");
	}
    dds.yllcorner = (double)field;
    invalid |= field.init(recList, "cellsize");
    dds.cellsize = (double)field;
    if(dds.cellsize <= 0)  invalid = -1;
    invalid |= field.init(recList, "NODATA_value");
    long  nodata = (long)field;
	if(nodata < -9999)  nodata = -9999;
    dds.reserved = (ratio > 1) ? 1 : 0;

    delete recList;

    if(invalid)
    {
        cout << fileName << ": Not ARC/INFO ASCII file" << endl;
        fclose(fi);  fclose(fp);  return;
    }

    // Set data description

    strncpy(dds.ld->theme, theme, 7);
    dds.ld->theme[7] = '\0';
    strcpy(dds.ld->shape, "grid");
    dds.ld->byteorder[0] = getHostByteOrder();
    dds.ld->coordef = coordef;

    strncpy(dds.ld->datatype, skip_blank(dataType), 7);
    dds.ld->datatype[7] = '\0';
    dds.ld->cellsize = (float)dds.cellsize;
    dds.ld->ratio = ratio;
    dds.ld->nodata = (short)nodata;

    dds.memory = 0;
    dds.data = strdup(dataName);

    // Transform data from ascii to binary

    readDataFromFile(fi, dds, fp);
    fclose(fi);  fclose(fp);

    // Report information to record file

    putData(dds);
}

int putDataToAsciiFile(DataDescription& dds, char *fileName)
{
    if( !fileName  ||  !dds.data)  return  -1;
    if(*dds.ld->shape != 'g')  
    {
	cout << dds.ld->shape << ": Non-grid shape not supported" << endl;
        return - 1;
    }

    ofstream  ofs(fileName);
    if( !ofs )  {perror(fileName);  return -1;}

    report_value(ofs, "ncols", dds.ncols);
    report_value(ofs, "nrows", dds.nrows);
    if(dds.ld->ratio > 1  &&  !dds.reserved)
    {
        report_value(ofs, "xllcorner", dds.xllcorner*dds.ld->ratio);
        report_value(ofs, "yllcorner", dds.yllcorner*dds.ld->ratio);
        report_value(ofs, "cellsize", dds.ld->cellsize);
    }
    else
    {
        report_value(ofs, "xllcorner", dds.xllcorner);
        report_value(ofs, "yllcorner", dds.yllcorner);
        report_value(ofs, "cellsize", dds.cellsize);
    }
    report_value(ofs, "NODATA_value", dds.ld->nodata);

    if( !dds.memory )
    {
        FILE  *fp = fopen(dds.data, "rb");
        if( !fp)  return  -1;
        fseek(fp, dds.offset, SEEK_SET);
        int  len = sizeof_type(dds.ld->datatype) * dds.ncols;
        char  *buffer = new char [len];
        int  bo = (*dds.ld->byteorder == getHostByteOrder()) ? 0 : 1;

        for(int j = 0; j < dds.nrows; j ++)
        {
            fread(buffer, len, 1, fp);
            switch(*dds.ld->datatype)
            {
            case    'b':
                {
                    BYTE  *data = (BYTE *)buffer;
    	            for(int i = 0; i < dds.ncols; i ++)
	                ofs << (unsigned short)data[i] << " ";
	            ofs << endl;
                }
                break;
            case    's':
                {
                    short  *data = (short *)buffer;
                    for(int i = 0; i < dds.ncols; i ++)
                    {
                        if(bo)  reverse2((char *)&data[i]);
                        ofs << data[i] << " ";
                    }
                    ofs << endl;
                }
                break;
            case    'i':
            case    'l':
                {
                    int  *data = (int *)buffer;
    	            for(int i = 0; i < dds.ncols; i ++)
                    {
                        if(bo)  reverse4((char *)&data[i]);
                        ofs << data[i] << " ";
                    }
	            ofs << endl;
                }
                break;
            case    'f':
                {
                    float  *data = (float *)buffer;
                    ofs << setprecision(3); 
    	            for(int i = 0; i < dds.ncols; i ++)
                    {
                        if(bo)  reverse4((char *)&data[i]);
                        ofs << data[i] << " ";
                    }
	            ofs << endl;
                }
                break;
            case    'd':
                {
                    double  *data = (double *)buffer;
                    ofs << setprecision(6);
    	            for(int i = 0; i < dds.ncols; i ++)
                    {
                        if(bo)  reverse8((char *)&data[i]);
                        ofs << data[i] << " ";
                    }
	            ofs << endl;
                }
                break;
            }
        }

        fclose(fp);   delete buffer;
        ofs.close();  return  0;
    }

    dds.hostByteOrder();
    switch(*dds.ld->datatype)
    {
    case    'b':
        {
            BYTE  *data = (BYTE *)dds.data;
            for(int j = 0, k = 0; j < dds.nrows; j ++)
            {
    	        for(int i = 0; i < dds.ncols; i ++)
	            ofs << (unsigned short)data[k ++] << " ";
	        ofs << endl;
            }
        }
        break;
    case    's':
        {
            short  *data = (short *)dds.data;
            for(int j = 0, k = 0; j < dds.nrows; j ++)
            {
    	        for(int i = 0; i < dds.ncols; i ++)
	            ofs << data[k ++] << " ";
	        ofs << endl;
            }
        }
        break;
    case    'i':
    case    'l':
        {
            int  *data = (int *)dds.data;
            for(int j = 0, k = 0; j < dds.nrows; j ++)
            {
    	        for(int i = 0; i < dds.ncols; i ++)
	            ofs << data[k ++] << " ";
	        ofs << endl;
            }
        }
        break;
    case    'f':
        {
            float  *data = (float *)dds.data;
            ofs << setprecision(3); 
            for(int j = 0, k = 0; j < dds.nrows; j ++)
            {
    	        for(int i = 0; i < dds.ncols; i ++)
	            ofs << data[k ++] << " ";
	        ofs << endl;
            }
        }
        break;
    case    'd':
        {
            double  *data = (double *)dds.data;
            ofs << setprecision(6);
            for(int j = 0, k = 0; j < dds.nrows; j ++)
            {
    	        for(int i = 0; i < dds.ncols; i ++)
	            ofs << data[k ++] << " ";
	        ofs << endl;
            }
        }
        break;
    }

    ofs.close();  return  0;
}

void dataFileToAsciiFile(char *dataName, char *fileName)
{
    DataDescription  *dds = getDataInfo(dataName);
    if( !dds )  return;
    
    putDataToAsciiFile(*dds, fileName);

    delete dds;
}

/////////////////////////////////////////////////

// Theme-Map-File  <-->  Data-File

/////////////////////////////////////////////////

void  themeFileToDataFile(char *themeName, char *dataName)
{
    char  buffer[256];

    if( !dataName  ||  !themeName)  return;

    ostrstream  os0(buffer, 256);
    os0 << themeName << ".tmf" << ends;
    FILE  *fr = fopen(buffer, "rb");
    if( !fr )  return;

    FILE  *fp = fopen(dataName, "wb");
    if( !fp )  {fclose(fr);  return;}

    ostrstream  os1(buffer, 256);
    os1 << dataName << ".rec" << ends;
    ofstream  ofs(buffer);
    if( !ofs )  {fclose(fr);  fclose(fp);  return;}

    // read head information

    VCharList  *recList = readRecordList(fr);
    if( !recList )  
    {
        ofs.close(); fclose(fr); fclose(fp); return;
    }
    LayerDescription  ld;
    int  invalid = 0;
    Field5  field(recList, "VERSION");
    if(strncmp(field.ptr(), "TMF", 3))  invalid = -1;
    field.init(recList, "THEME");
    strncpy(ld.theme, field.ptr(), 10);
    invalid |= field.init(recList, "SHAPE");
    strncpy(ld.shape, field.ptr(), 7);
    ld.byteorder[0] = getHostByteOrder();
    invalid |= field.init(recList, "COORDEF");
    ld.coordef = (float)field;

    if(ld.shape[0] == 'g')
    {
        invalid |= field.init(recList, "DATATYPE");
        strncpy(ld.datatype, field.ptr(), 7);
        invalid |= field.init(recList, "CELLSIZE");
	ld.cellsize = (float)field;
	field.init(recList, "RATIO");
        ld.ratio = (int)field;
        if(ld.ratio < 1)  ld.ratio = 1;
        field.init(recList, "NODATA");
        ld.nodata = (int)field;
    }
    delete recList;
    if(invalid)  
    {
        ofs.close(); fclose(fr); fclose(fp); return;
    }

    // record head information

    report_value(ofs, "THEME", ld.theme);
    report_value(ofs, "SHAPE", ld.shape);
    if(*ld.byteorder == 'I')
        report_value(ofs, "BYTEORDER", "Intel");
    else
        report_value(ofs, "BYTEORDER", "Motorola");
    report_value(ofs, "COORDEF", ld.coordef);

    if(ld.shape[0] == 'g')
    {
        report_value(ofs, "DATATYPE", ld.datatype);
        report_value(ofs, "CELLSIZE", ld.cellsize);
        report_value(ofs, "RATIO", ld.ratio);
        report_value(ofs, "NODATA", ld.nodata);
    }

    // for each object ...

    while(1)
    {
        if(goNextObject(fr) == -1)  break;
        VCharList  *recList = readRecordList(fr);
        if( !recList )  break;
        DataDescription  dds;
        if(ld.shape[0] == 'g')
        {
            field.init(recList, "NCOLS");
            dds.ncols = (int)field;
            recList->delete_node();
            field.init(recList, "NROWS");
            dds.nrows = (int)field;
            recList->delete_node();
            field.init(recList, "XLLCORNER");
            dds.xllcorner = (double)field;
            recList->delete_node();
            field.init(recList, "YLLCORNER");
            dds.yllcorner = (double)field;
            recList->delete_node();
        }
        else
        {
            field.init(recList, "NPOINTS");
            dds.ncols = (int)field;
            recList->delete_node();
            field.init(recList, "NENTITIES");
            dds.nrows = (int)field;
            recList->delete_node();
        }
        if(dds.ncols < 1  ||  dds.nrows < 1)
        {
            delete recList;  break;
        }

        // record attributes

        ofs << endl << "<OBJECT>" << endl << endl;
        if(ld.shape[0] == 'g')
        {
            report_value(ofs, "NCOLS", dds.ncols);
            report_value(ofs, "NROWS", dds.nrows);
            report_value(ofs, "XLLCORNER", dds.xllcorner);
            report_value(ofs, "YLLCORNER", dds.yllcorner);
        }
        else
        {
            report_value(ofs, "NPOINTS", dds.ncols);
            report_value(ofs, "NENTITIES", dds.nrows);
        }

        int  offset = ftell(fp);
        report_value(ofs, "DATAOFF", offset);
        ofs << endl;
        for(recList->top(); recList->ptr; recList->skip())
        {
            vchar  *p = (vchar *)recList->item();
            BYTE  *name = (BYTE *)p->arr;
            for(int i = 0; i < 15; i ++)
            {
                if( !name[i] )  break;
                if(name[i] >= 'a' && name[i] <= 'z')
                    name[i] -= 0x20;
            }
            report_value(ofs, p->arr, p->arr+40);
        }
        delete recList;

        // record spatial data

        dds.ld = &ld;
        readDataFromFile(fr, dds, fp);
	dds.ld = NULL;
    }

    ofs.close();  fclose(fr);  fclose(fp);
}

void dataFileToThemeFile(char *dataName, char *themeName)
{
    if( !dataName  ||  !themeName)  return;

    LayerDescription  ld;
    FILE  *fr = readThemeFile(dataName, ld);
    if( !fr )  return;

    FILE  *fp = fopen(dataName, "rb");
    if( !fp )  {fclose(fr);  return;}

    char  buffer[256];
    ostrstream  os1(buffer, 256);
    os1 << themeName << ".tmf" << ends;
    ofstream  ofs(buffer);
    if( !ofs )  {fclose(fr);  fclose(fp);  return;}
    ofs.setf(ios::fixed, ios::floatfield);

    // report head information

    report_value(ofs, "VERSION", "TMF1.0");
    report_value(ofs, "THEME", ld.theme);
    report_value(ofs, "SHAPE", ld.shape);
    report_value(ofs, "COORDEF", ld.coordef);

    if(ld.shape[0] == 'g')
    {
        report_value(ofs, "DATATYPE", ld.datatype);
        report_value(ofs, "CELLSIZE", ld.cellsize);
        report_value(ofs, "RATIO", ld.ratio);
        report_value(ofs, "NODATA", ld.nodata);
    }

    int  bo = (ld.byteorder[0] == getHostByteOrder()) ? 0 : 1;

    // for each object ...

    Field5  field;
    while(1)
    {
        if(goNextObject(fr) == -1)  break;
        VCharList  *recList = readRecordList(fr);
        if( !recList )  break;

        DataDescription  dds;
	dds.ld = &ld;
	dds.list = recList;

        if(ld.shape[0] == 'g')
        {
            field.init(recList, "NCOLS");
            dds.ncols = (int)field;
            recList->delete_node();
            field.init(recList, "NROWS");
            dds.nrows = (int)field;
            recList->delete_node();
            field.init(recList, "XLLCORNER");
            dds.xllcorner = (double)field;
            recList->delete_node();
            field.init(recList, "YLLCORNER");
            dds.yllcorner = (double)field;
            recList->delete_node();
        }
        else
        {
            field.init(recList, "NPOINTS");
            dds.ncols = (int)field;
            recList->delete_node();
            field.init(recList, "NENTITIES");
            dds.nrows = (int)field;
            recList->delete_node();
        }

        field.init(recList, "DATAOFF");
        int  offset = (int)field;
        recList->delete_node();

        // record attributes

        ofs << endl << "<OBJECT>" << endl << endl;
        if(ld.shape[0] == 'g')
        {
            report_value(ofs, "NCOLS", dds.ncols);
            report_value(ofs, "NROWS", dds.nrows);
            report_value(ofs, "XLLCORNER", dds.xllcorner);
            report_value(ofs, "YLLCORNER", dds.yllcorner);
        }
        else
        {
            report_value(ofs, "NPOINTS", dds.ncols);
            report_value(ofs, "NENTITIES", dds.nrows);
        }

        for(recList->top(); recList->ptr; recList->skip())
        {
            vchar  *p = (vchar *)recList->item();
            report_value(ofs, p->arr, p->arr+40);
        }
        ofs << endl;

        // report spatial data

        fseek(fp, offset, SEEK_SET);
        if(ld.shape[0] == 'g')
        {
	    long  ncols = dds.ncols;
	    long  nrows = dds.nrows;
            unsigned long  len = sizeof_type(ld.datatype) * ncols;
            char  *buffer = new char [len];

            for(int j = 0; j < nrows; j ++)
            {
                if(fread(buffer, 1, len, fp) < len)  break;
                switch(*ld.datatype)
                {
                case    'b':
                    {
                        BYTE  *data = (BYTE *)buffer;
    	                for(int i = 0; i < ncols; i ++)
	                    ofs << (unsigned short)data[i] << " ";
	                ofs << endl;
                    }
                    break;
                case    's':
                    {
                        short  *data = (short *)buffer;
                        for(int i = 0; i < ncols; i ++)
                        {
                            if(bo)  reverse2((char *)&data[i]);
                            ofs << data[i] << " ";
                        }
                        ofs << endl;
                    }
                    break;
                case    'i':
                case    'l':
                    {
                        int  *data = (int *)buffer;
    	                for(int i = 0; i < ncols; i ++)
                        {
                            if(bo)  reverse4((char *)&data[i]);
                            ofs << data[i] << " ";
                        }
	                ofs << endl;
                    }
                    break;
                case    'f':
                    {
                        float  *data = (float *)buffer;
                        ofs << setprecision(3); 
    	                for(int i = 0; i < ncols; i ++)
                        {
                            if(bo)  reverse4((char *)&data[i]);
                            ofs << data[i] << " ";
                        }
	                ofs << endl;
                    }
                    break;
                case    'd':
                    {
                        double  *data = (double *)buffer;
                        ofs << setprecision(6);
    	                for(int i = 0; i < ncols; i ++)
                        {
                            if(bo)  reverse8((char *)&data[i]);
                            ofs << data[i] << " ";
                        }
	                ofs << endl;
                    }
                    break;
                }
            }
            delete buffer;
        }
        else
        {
            unsigned long  len = dds.sizeofData();
            char  *buffer = new char [len];
            if(fread(buffer, 1, len, fp) < len)  break;
            char  *src = buffer;

            for(int j = 0, npoints = 0; j < dds.nrows; j ++)
            {
		Entity  *edata = (Entity *)src;
                if(bo)
		{
		    reverse4( (char *)&edata->e_id );
		    reverse4( (char *)&edata->npts );
		}
		src += sizeof(long) * 2 + sizeof(POINT3) * edata->npts;
                ofs << edata->e_id << "  " << edata->npts << endl;
                ofs << setprecision(15);
                for(int i = 0; i < edata->npts; i ++, npoints ++)
                {
		     if(npoints >= dds.ncols)  break;

                     if(bo)
                     {
                         reverse8((char *)&edata->pt3[i].x);
                         reverse8((char *)&edata->pt3[i].y);
                         reverse8((char *)&edata->pt3[i].z);
                     }
                     ofs << edata->pt3[i].x << "  ";
                     ofs << edata->pt3[i].y << "  ";
                     ofs << edata->pt3[i].z << endl;
                }
            }
            delete buffer;
        }
	dds.ld = NULL;
    }

    ofs.close();  fclose(fr);  fclose(fp);
}

/////////////////////////////////////////////////

//  GridData members

/////////////////////////////////////////////////

GridData::GridData() 
{
    dd = NULL;  native = 0;

    data = NULL;

    data_s = NULL;
    data_l = NULL;
    data_f = NULL;
    data_d = NULL;
}

GridData::GridData(DataDescription *dds, int asNative) 
{
    dd = NULL;  native = 0;
    
    data = NULL;

    this->init(dds, asNative);
}

GridData::GridData(char *dataName) 
{
    dd = NULL;  native = 0;
    
    data = NULL;

    this->init(dataName);
}

GridData::~GridData()
{
    if(dd && native)  delete dd;
    dd = NULL;  native = 0;

    if(data)  delete data;
    data = NULL;

    data_s = NULL;
    data_l = NULL;
    data_f = NULL;
    data_d = NULL;
}

void GridData::init(DataDescription *dds, int asNative)
{
    if(dd && native)  delete dd;
    dd = NULL;  native = 0;

    if(data)  delete data;
    data = NULL;

    data_s = NULL;
    data_l = NULL;
    data_f = NULL;
    data_d = NULL;

    if(dds == NULL)  return;
    if(dds->ld->shape[0] != 'g' || !dds->data || !dds->memory)  return;

    dd = dds;

    data = new char* [dds->nrows];
    data[0] = dds->data;
    int  bytes_per_line = dds->bytesPerLine();
    for(int k = 1; k < dds->nrows; k ++)
        data[k] = data[k-1] + bytes_per_line;

    if(dds->ld->datatype[0] == 's')  data_s = (short  **)data;
    if(dds->ld->datatype[0] == 'l')  data_l = (long   **)data;
    if(dds->ld->datatype[0] == 'f')  data_f = (float  **)data;
    if(dds->ld->datatype[0] == 'd')  data_d = (double **)data;

    dds->normalUnits();

    if(asNative)  native = 1;
}

void GridData::init(char *dataName)
{
    DataDescription  *dds = getData(dataName);

    this->init(dds, 1);

    if( !data )
    {
        if(dds)  delete dds;
    }
}

void GridData::initMSL(DataDescription *dds, int sublayer)
{
    if(dd && native)  delete dd;
    dd = NULL;  native = 0;

    if(data)  delete data;
    data = NULL;

    data_s = NULL;
    data_l = NULL;
    data_f = NULL;
    data_d = NULL;

    if(dds == NULL)  return;
    if(dds->ld->shape[0] != 'g' || !dds->data || !dds->memory)  return;

    if(sublayer < 0  ||  sublayer > dds->ld->sublayers)  return;

    dd = dds;

    int  bytes_per_line = dds->bytesPerLine();
    data = new char* [dds->nrows];
    data[0] = dds->data + dds->sizeofSubLayer() * sublayer;
    for(int k = 1; k < dds->nrows; k ++)
        data[k] = data[k-1] + bytes_per_line;

    if(dds->ld->datatype[0] == 's')  data_s = (short **)data;
    if(dds->ld->datatype[0] == 'l')  data_l = (long **)data;
    if(dds->ld->datatype[0] == 'f')  data_f = (float **)data;
    if(dds->ld->datatype[0] == 'd')  data_d = (double **)data;

    dds->normalUnits();
}

int GridData::getDataInt(int col, int row)
{
    int  val = dd->ld->nodata;
    if(col < 0  ||  row < 0  ||  col >= dd->ncols  ||  row >= dd->nrows)  return val;

    switch (dd->ld->datatype[0])
    {
    case    's':
        val = data_s[row][col];
        break;
    case    'l':
    case    'i':
        val = data_l[row][col];
        break;
    case    'f':
        val = (int)data_f[row][col];
        break;
    case    'd':
        val = (int)data_d[row][col];
        break;
    default:
        if(strcmp(dd->ld->datatype, "tbit") == 0)
        {
            val = data[row][col >> 3];
            val = val & (0x80 >> (col & 0x07));
            if(val)  val = 1;
            break;
        }
        val = (BYTE)data[row][col];
        break;
    }

    return val;
}

void GridData::setDataBit(int col, int row, int val)
{
    if(col < 0  ||  row < 0  ||  col >= dd->ncols  ||  row >= dd->nrows)  return;
    if(strcmp(dd->ld->datatype, "tbit") != 0)  return;

    int  msk = 0x80 >> (col & 0x07);
    if(val)  data[row][col>>3] |= msk;
    else  data[row][col>>3] &= (~msk);
}

int GridData::getDataInt(double x, double y)
{
    return (int)getDataCell(x, y);
}

double GridData::getDataCell(double x, double y)
{
    double  val = dd->ld->nodata;

    double  u = (x - dd->xllcorner) / dd->cellsize + 0.5;
    double  v = (y - dd->yllcorner) / dd->cellsize + 0.5;
    if(u < 0  ||  v < 0  ||  u >= dd->ncols  ||  v >= dd->nrows)  return val;

    int  c_x = (int)u;
    int  r_y = dd->nrows - 1 - (int)v;

    switch (dd->ld->datatype[0])
    {
    case    's':
        val = data_s[r_y][c_x];
        break;
    case    'l':
    case    'i':
        val = data_l[r_y][c_x];
        break;
    case    'f':
        val = data_f[r_y][c_x];
        break;
    case    'd':
        val = data_d[r_y][c_x];
        break;
    default:
        if(strcmp(dd->ld->datatype, "tbit") == 0)
        {
            int  valI = data[r_y][c_x >> 3];
            valI = valI & (0x80 >> (c_x & 0x07));
            val = valI ? 1.0 : 0;
            break;
        }
        val = (BYTE)data[r_y][c_x];
        break;
    }

    return val;
}

double GridData::getDataCell2(double x, double y)
{
    short  nodata_value = dd->ld->nodata;

    double  u = (x - dd->xllcorner) / dd->cellsize;
    double  v = (y - dd->yllcorner) / dd->cellsize;
    v = dd->nrows - 1 - v;
    if(u < 0  ||  v < 0)  return nodata_value;

    int  c_x = (int)u;  double  du = u - c_x;
    int  r_y = (int)v;  double  dv = v - r_y;
    if(c_x >= dd->ncols-1 || r_y >= dd->nrows-1)  return nodata_value;

    double  h1, h2, h3, h4;

    switch (dd->ld->datatype[0])
    {
    case    's':
        h1 = data_s[ r_y ][c_x];  h3 = data_s[ r_y ][c_x+1];
        h2 = data_s[r_y+1][c_x];  h4 = data_s[r_y+1][c_x+1];
        break;
    case    'l':
    case    'i':
        h1 = data_l[ r_y ][c_x];  h3 = data_l[ r_y ][c_x+1];
        h2 = data_l[r_y+1][c_x];  h4 = data_l[r_y+1][c_x+1];
        break;
    case    'f':
        h1 = data_f[ r_y ][c_x];  h3 = data_f[ r_y ][c_x+1];
        h2 = data_f[r_y+1][c_x];  h4 = data_f[r_y+1][c_x+1];
        break;
    case    'd':
        h1 = data_d[ r_y ][c_x];  h3 = data_d[ r_y ][c_x+1];
        h2 = data_d[r_y+1][c_x];  h4 = data_d[r_y+1][c_x+1];
        break;
    default:
        h1 = (BYTE)data[ r_y ][c_x];  h3 = (BYTE)data[ r_y ][c_x+1];
        h2 = (BYTE)data[r_y+1][c_x];  h4 = (BYTE)data[r_y+1][c_x+1];
        break;
    }
    
    if( h1 <= nodata_value  ||  h3 <= nodata_value  ||
        h2 <= nodata_value  ||  h4 <= nodata_value )
        return nodata_value;

    double  h12 = (h2 - h1) * dv + h1;
    double  h34 = (h4 - h3) * dv + h3;

    return ((h34 - h12) * du + h12);
}

/////////////////////////////////////////////////

//  Vector Data

/////////////////////////////////////////////////

VectData::VectData() 
{
    dd = NULL;  native = 0;
    data = NULL;
    npoints = nentities = 0;
}

VectData::VectData(DataDescription* dds)
{
    dd = NULL;  native = 0;
    data = NULL;
    npoints = nentities = 0;

    this->init(dds);
}

VectData::VectData(char *dataName)
{
    dd = NULL;  native = 0;
    data = NULL;
    npoints = nentities = 0;

    this->init(dataName);
}

VectData::~VectData() 
{
    if(dd && native)  delete dd;
    dd = NULL;  native = 0;

    if(data)  delete data;
    data = NULL;
}

void VectData::init(DataDescription *dds)
{
    if(dd && native)  delete dd;
    dd = NULL;  native = 0;
    npoints = nentities = 0;

    if(data)  delete data;
    data = NULL;

    if(dds == NULL)  return;
    if(dds->ld->shape[0] == 'g' || !dds->memory)  return;

    dds->hostByteOrder();
    dd = dds;

    npoints = dd->ncols;
    nentities = dd->nrows;
    xllbounds = dd->xllcorner;
    yllbounds = dd->yllcorner;
    xtrbounds = dd->cellsize;
    ytrbounds = dd->reserved;

    data = new Entity* [nentities];
    char  *p = dds->data;
    for(int k = 0; k < nentities; k ++)
    {
        data[k] = (Entity *)p;
        p += sizeof(POINT3) * data[k]->npts + sizeof(long) * 2;
    }
}

void VectData::init(char *dataName)
{
    DataDescription  *dds = getData(dataName);

    this->init(dds);

    if( !data ) {if(dds)  delete dds;}
    else  this->native = 1;
}

///////////////////////////////////////////////////////

// Get seamless map from grid data list

///////////////////////////////////////////////////////

GridData *getSeamless(DataList *dataList)
{
    if( !dataList )  return NULL;

    DataDescription  *dds = dataList->first();

    if( !dds )  return NULL;

    if(*dds->ld->shape != 'g')  return NULL;

    if(dataList->count() == 1)
    {
        dataList->delete_node();
        dataList->ld = NULL;
        return (new GridData(dds, 1));
    }

    dds->normalUnits();
    double  csz = dds->cellsize;
    double  xll = dds->xllcorner;
    double  yll = dds->yllcorner;
    double  xtr = xll + (dds->ncols - 1) * csz;
    double  ytr = yll + (dds->nrows - 1) * csz;

    double  scf_xll = xll;
    double  scf_yll = yll;
    double  scf_xtr = xtr;
    double  scf_ytr = ytr;

    for(dds = dataList->next(); dds; dds = dataList->next())
    {
        dds->normalUnits();
        xll = dds->xllcorner;
        yll = dds->yllcorner;
        xtr = xll + (dds->ncols - 1) * csz;
        ytr = yll + (dds->nrows - 1) * csz;
        if(xll < scf_xll)  scf_xll = xll;
        if(yll < scf_yll)  scf_yll = yll;
        if(xtr > scf_xtr)  scf_xtr = xtr;
        if(ytr > scf_ytr)  scf_ytr = ytr;
    }

    dds = new DataDescription();
    dds->ld = new LayerDescription();
    *(dds->ld) = *(dataList->ld);

    dds->ncols = (int)((scf_xtr - scf_xll + 0.1*csz) / csz) + 1;
    dds->nrows = (int)((scf_ytr - scf_yll + 0.1*csz) / csz) + 1;
    dds->xllcorner = scf_xll;
    dds->yllcorner = scf_yll;
    dds->cellsize = csz;
    dds->reserved = 0;

    dds->allocateData();
    if( !dds->data )
    {
        delete dds;  return NULL;
    }

    GridData  *grd = new GridData(dds, 1);

    // Set NODATA_value

    int  k;

    switch(*dds->ld->datatype)
    {
    case    'b':
        {
            BYTE  nd = (BYTE)dds->ld->nodata;
            BYTE  **dest = (BYTE **)grd->data;
            int  colLen = dds->ncols;
            for(k = 0; k < dds->ncols; k ++)
                dest[0][k] = nd;
            for(k = 1; k < dds->nrows; k ++)
                memcpy(dest[k], dest[0], colLen);
        }
        break;
    case    's':
        {
            short  nd = (short)dds->ld->nodata;
            short  **dest = grd->data_s;
            int  colLen = dds->ncols * 2;
            for(k = 0; k < dds->ncols; k ++)
                dest[0][k] = nd;
            for(k = 1; k < dds->nrows; k ++)
                memcpy(dest[k], dest[0], colLen);
        }
        break;
    case    'i':
    case    'l':
        {
            long  nd = (int)dds->ld->nodata;
            long  **dest = grd->data_l;
            int  colLen = dds->ncols * 4;
            for(k = 0; k < dds->ncols; k ++)
                dest[0][k] = nd;
            for(k = 1; k < dds->nrows; k ++)
                memcpy(dest[k], dest[0], colLen);
        }
        break;
    case    'f':
        {
            float  nd = (float)dds->ld->nodata;
            float  **dest = grd->data_f;
            int  colLen = dds->ncols * 4;
            for(k = 0; k < dds->ncols; k ++)
                dest[0][k] = nd;
            for(k = 1; k < dds->nrows; k ++)
                memcpy(dest[k], dest[0], colLen);
        }
        break;
    case    'd':
        {
            double  nd = (double)dds->ld->nodata;
            double  **dest = grd->data_d;
            int  colLen = dds->ncols * 8;
            for(k = 0; k < dds->ncols; k ++)
                dest[0][k] = nd;
            for(k = 1; k < dds->nrows; k ++)
                memcpy(dest[k], dest[0], colLen);
        }
        break;
    }

    double  x0 = scf_xll - 0.5 * csz;
    double  y0 = scf_yll - 0.5 * csz;

    for(DataDescription *p = dataList->first(); p; p = dataList->next())
    {
        int  c0 = (int)((p->xllcorner - x0) / csz);
        int  r0 = (int)((p->yllcorner - y0) / csz);
        int  c1 = c0 + p->ncols;
        int  r1 = r0 + p->nrows;

        GridData  grd_s(p);

        switch(*dds->ld->datatype)
        {
        case    'b':
            {
                BYTE  **src = (BYTE **)grd_s.data;
                BYTE  **dest = (BYTE **)grd->data;
                BYTE  nd = (BYTE)dds->ld->nodata;
                for(int j = r0, J = 0; j < r1; j ++, J ++)
                {
                    int  V = p->nrows - 1 - J;
                    int  v = dds->nrows - 1 - j;
                    for(int i = c0, I = 0; i < c1; i ++, I ++)
                    {
			if(src[V][I] > nd)  dest[v][i] = src[V][I];
                    }
                }
            }
            break;
        case    's':
            {
                short  **src = grd_s.data_s;
                short  **dest = grd->data_s;
                short  nd = (short)dds->ld->nodata;
                for(int j = r0, J = 0; j < r1; j ++, J ++)
                {
                    int  V = p->nrows - 1 - J;
                    int  v = dds->nrows - 1 - j;
                    for(int i = c0, I = 0; i < c1; i ++, I ++)
                    {
                        if(src[V][I] > nd)  dest[v][i] = src[V][I];
                    }
                }
            }
            break;
        case    'i':
        case    'l':
            {
                long  **src = grd_s.data_l;
                long  **dest = grd->data_l;
                int  nd = (int)dds->ld->nodata;
                for(int j = r0, J = 0; j < r1; j ++, J ++)
                {
                    int  V = p->nrows - 1 - J;
                    int  v = dds->nrows - 1 - j;
                    for(int i = c0, I = 0; i < c1; i ++, I ++)
                    {
                        dest[v][i] = src[V][I];
                    }
                }
            }
            break;
        case    'f':
            {
                float  **src = grd_s.data_f;
                float  **dest = grd->data_f;
                float  nd = (float)dds->ld->nodata;
                for(int j = r0, J = 0; j < r1; j ++, J ++)
                {
                    int  V = p->nrows - 1 - J;
                    int  v = dds->nrows - 1 - j;
                    for(int i = c0, I = 0; i < c1; i ++, I ++)
                    {
                        if(src[V][I] > nd)  dest[v][i] = src[V][I];
                    }
                }
            }
            break;
        case    'd':
            {
                double  **src = grd_s.data_d;
                double  **dest = grd->data_d;
                double  nd = (double)dds->ld->nodata;
                for(int j = r0, J = 0; j < r1; j ++, J ++)
                {
                    int  V = p->nrows - 1 - J;
                    int  v = dds->nrows - 1 - j;
                    for(int i = c0, I = 0; i < c1; i ++, I ++)
                    {
                        if(src[V][I] > nd)  dest[v][i] = src[V][I];
                    }
                }
            }
            break;
        }
    }

    return grd;
}

/*
** 初值：无数据
*/
void DataDescription::set_NODATA_value()
{
    LayerDescription&  ld = *(this->ld);

    if(strcmp(ld.datatype, "tbit") == 0)
    {
        memset(this->data, 0, sizeofData());
        return;
    }

    long  total_rows = this->nrows * ld.sublayers;

    int  k;
    switch( ld.datatype[0] )
    {
    case    'b':
        {
            BYTE  nd = (BYTE)ld.nodata;
            BYTE  *dest = (BYTE *)this->data;
            int   colLen = this->ncols;
            for(k = 0; k < this->ncols; k ++)
                dest[k] = nd;
            for(k = 1; k < total_rows; k ++)
                memcpy(&dest[k*colLen], &dest[0], colLen);
        }
        break;
    case    's':
        {
            short  nd = (short)ld.nodata;
            short  *dest = (short *)this->data;
            int  colLen = this->ncols * 2;
            if(getHostByteOrder() != ld.byteorder[0])
                reverse2((char *)&nd);
            for( k = 0; k < this->ncols; k ++)
                dest[k] = nd;
            for(k = 1; k < total_rows; k ++)
                memcpy(&dest[k*this->ncols], &dest[0], colLen);
        }
        break;
    case    'i':
    case    'l':
        {
            long  nd = (long)ld.nodata;
            long  *dest = (long *)this->data;
            int  colLen = this->ncols * 4;
            if(getHostByteOrder() != ld.byteorder[0])
                reverse4((char *)&nd);
            for(k = 0; k < this->ncols; k ++)
                dest[k] = nd;
            for(k = 1; k < total_rows; k ++)
                memcpy(&dest[k*this->ncols], &dest[0], colLen);
        }
        break;
    case    'f':
        {
            float  nd = (float)ld.nodata;
            float  *dest = (float *)this->data;
            int  colLen = this->ncols * 4;
            if(getHostByteOrder() != ld.byteorder[0])
                reverse4((char *)&nd);
            for(k = 0; k < this->ncols; k ++)
                dest[k] = nd;
            for(k = 1; k < total_rows; k ++)
                memcpy(&dest[k*this->ncols], &dest[0], colLen);
        }
        break;
    case    'd':
        {
            double  nd = (double)ld.nodata;
            double  *dest = (double *)this->data;
            int  colLen = this->ncols * 8;
            if(getHostByteOrder() != ld.byteorder[0])
                reverse8((char *)&nd);
            for(k = 0; k < this->ncols; k ++)
                dest[k] = nd;
            for(k = 1; k < total_rows; k ++)
                memcpy(&dest[k*this->ncols], &dest[0], colLen);
        }
        break;
    }
}

/*
** 从多个文件访问数据，减抽样、拼接（支持多子层）
*/
void merge_from_file(DataDescription& dds, TileDescription *td, int nTiles, long shrink)
{
    double  csk  = dds.ld->cellsize;        // 目标数据的分辨率
    double  CS = csk / (double)shrink;      // 原始数据的分辨率

    double  x0 = dds.xllcorner;             // 目标数据范围左下角点
    double  y0 = dds.yllcorner;             // 目标数据范围左下角点

    int  to_reverse = getHostByteOrder() != dds.ld->byteorder[0];

    char  bin_nodata[8] = {0};
    switch(dds.ld->datatype[0])
    {
    case   's':
        {
            short  nodata = dds.ld->nodata;
            if(to_reverse)  reverse2((char *)&nodata);
            memcpy(&bin_nodata[0], &nodata, 2);
        }
        break;
    case   'i':
    case   'l':
        {
            long  nodata = dds.ld->nodata;
            if(to_reverse)  reverse4((char *)&nodata);
            memcpy(&bin_nodata[0], &nodata, 4);
        }
        break;
    case   'f':
        {
            float  nodata = dds.ld->nodata;
            if(to_reverse)  reverse4((char *)&nodata);
            memcpy(&bin_nodata[0], &nodata, 4);
        }
        break;
    case   'd':
        {
            double  nodata = dds.ld->nodata;
            if(to_reverse)  reverse8((char *)&nodata);
            memcpy(&bin_nodata[0], &nodata, 8);
        }
        break;
    default:
        bin_nodata[0] = (char)dds.ld->nodata;
        break;
    }

    for(int k = 0; k < nTiles; k ++)   
    {
        if(td[k].offset < 0)  continue;

        // 在目标中的偏移(i0, j0)，假定左下角点(0, 0)
        // 在图幅内的偏移(II, JJ)，假定左下角点(0, 0)

        long    II, JJ;
        long    i0, j0;

        if(td[k].xllcorner < x0)
        {
            II = (int)((x0 - td[k].xllcorner) / CS + 0.5);
            i0 = 0;
        }
        else
        {
            II = 0;
            i0 = (int)((td[k].xllcorner - x0) / csk + 0.5);
        }

        if(td[k].yllcorner < y0)
        {
            JJ = (int)((y0 - td[k].yllcorner) / CS + 0.5);
            j0 = 0;
        }
        else
        {
            JJ = 0;
            j0 = (int)((td[k].yllcorner - y0) / csk + 0.5);
        }

        // 被访问区域在目标中的尺寸（ncols、nrows）

        long  ncols, nrows;

        ncols = (int)((td[k].xtrcorner - x0) / csk) - i0 + 1;
        nrows = (int)((td[k].ytrcorner - y0) / csk) - j0 + 1;

        if(ncols + i0 > dds.ncols)  ncols = dds.ncols - i0;
        if(nrows + j0 > dds.nrows)  nrows = dds.nrows - j0;

        if(ncols <= 0  ||  nrows <= 0)  continue;

        // 访问图形数据

        int  nC = (ncols - 1) * shrink + 1;

        int  cellen = sizeof_type(dds.ld->datatype);
        int  src_line_bytes = nC * cellen;

        FILE  *fp = fopen(td[k].data, "rb");
        if( !fp )  continue;

        char  *buffer = new char [src_line_bytes];

		long  sizeofSL = td[k].nrows * td[k].ncols * sizeof_type(dds.ld->datatype);

        for(int l = 0; l < dds.ld->sublayers; l ++)
        {
            char  *base = dds.data + dds.sizeofSubLayer() * l;
            long  offset = td[k].offset +sizeofSL * l;

            for(int j = 0; j < nrows; j ++)
            {
                // 目标数据存储的行偏移

                long  mj = dds.nrows-1 - (j0 + j);
                char  *dest = base + (mj * dds.ncols + i0) * cellen;

                // 图幅中当前访问行的偏移

                long  mJ = td[k].nrows-1 - (JJ + j * shrink);
                long  off = offset + (mJ * td[k].ncols + II) * cellen;

                // 文件指针定位，读取一行原始数据

                fseek(fp, off, SEEK_SET);
                fread(buffer, src_line_bytes, 1, fp);

                // 复制（或者减抽样）到目标中

                int  I = 0;
                for(int i = 0; i < ncols; i ++, I += shrink)
                {
                    char  *pp = buffer + I * cellen;
                    if(memcmp(pp, &bin_nodata[0], cellen) == 0)  continue;
                    memcpy(dest + i*cellen, pp, cellen);
                }
            }
        } // 每一子层

        delete buffer;
        fclose(fp);
    }
}
