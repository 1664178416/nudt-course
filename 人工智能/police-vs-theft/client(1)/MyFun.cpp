//MyFun.cpp
#include "StdAfx.h"
#include "MyFun.h"
#include "math.h"

///取得地形数据中的最大值.
int GetMax(short** ppShort,int nWidth,int nHeight)
{
//ppShort－－－原始数据矩阵。
//nWidth－－－数据矩阵宽度。
//nHeight－－－数据矩阵高度。
	int i,j;
	int nMax=ppShort[0][0];
	for(i=0;i<nHeight;i++)
	{
		for(j=0;j<nWidth;j++)
		{
			if(ppShort[i][j]>nMax) nMax=ppShort[i][j];
		}
	}
	return nMax;
	
}


//由经纬度得到高程.
int FromLLPtoHeight(double x,double y,short** ppShort,double xCorner,double yCorner,
					double cellSize,int nHeight)
{
//x,y---经纬度。
//ppShort---原始数据数组。
//xCorner,yCorner---原始数据左下角的经纬度坐标。
//cellSize---原始数据格网的步长。
//nHeight---原始数据的高度。

	int j=int((x-xCorner)/cellSize+0.5);
	int i=nHeight-1-int((y-yCorner)/cellSize+0.5);
    return ppShort[i][j];
}

