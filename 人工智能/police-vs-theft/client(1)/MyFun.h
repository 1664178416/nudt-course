#ifndef _include_myfun_h_
#define _include_myfun_h_

#ifndef  PI
#define  PI 3.1415926535898
#endif


#include "stdafx.h"
//MyFun.h
#include "math.h"

#define WIDTH 1120 //全局图中航线长方向的设备单位长度.


///取得地形数据中的最大值.
int GetMax(short** ppShort,int nWidth,int nHeight);


//由经纬度得到高程.
int FromLLPtoHeight(double x,double y,short** ppShort,double xCorner,double yCorner,
					double cellSize,int nHeight);

#endif



