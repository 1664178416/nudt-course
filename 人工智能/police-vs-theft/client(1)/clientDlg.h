// clientDlg.h : header file
//

#if !defined(AFX_CLIENTDLG_H__DABB0C52_DA57_4B00_AA0A_DCC14F133617__INCLUDED_)
#define AFX_CLIENTDLG_H__DABB0C52_DA57_4B00_AA0A_DCC14F133617__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000
#include <afxtempl.h>
#include "sde.h"

/////////////////////////////////////////////////////////////////////////////
// CClientDlg dialog
#define UM_ClientSOCK WM_USER+100


struct Move_position
{
	double c_long = 0;         //终点经度坐标
	double c_lat = 0;          //终点纬度坐标
	Move_position() : c_long(0.0), c_lat(0.0) {}
	Move_position(double a, double b) : c_long(a), c_lat(b) {}
};

typedef CList<Move_position, Move_position&> MoveList;   //Agent移动序列

typedef struct tagCINFO //定义客户端信息结构
{
	char c_Name[MAX_COMPUTERNAME_LENGTH + 1];      //客户端主机名
	int role;             //角色(0警察，1逃犯)
	CString map_name;     //所选地图
	in_addr  c_IP;        //客户端IP地址
	double c_long = 0;         //经度坐标
	double c_lat = 0;          //纬度坐标
	int  c_eyeshot;      //视野范围（单元格）
	int  c_stepLength;    //最大步长（单元格）
	MoveList c_friendPosition;    //其他警察同行的位置
	MoveList c_enemyPosition;     //看到的敌方的位置

} C_INFO;


class CClientDlg : public CDialog
{
	// Construction
public:
	BOOL ToServerRegisterMessage(SOCKET s, C_INFO* info);
	BOOL ToServerDate(SOCKET s, MoveList* list);
	BOOL CreateSocket();
	CClientDlg(CWnd* pParent = NULL);	// standard constructor
	BOOL InitializeSocket();
	CString GetSuffix(CString PathName);//获得文件名的后缀


	SOCKADDR_IN severAddr;
	SOCKET m_socket;
	C_INFO client_info;            //客户端消息结构体
	BOOL register_success;            //注册成功标志
	BOOL m_bConnect;                  //连接成功标志
	BOOL m_bInit;                  //连接成功标志
	BOOL s_registerRequire;        //注册成功标志
	CString m_strFilePath;         //地图文件路径字符串
	CString m_strFileName;         //地图文件名称字符串       
	MoveList m_moveList;			//Agent移动序列

public:
	double Distance3(double x1, double y1, double h1, double x2, double y2, double h2);
	double Distance(double x1, double y1, double x2, double y2);
	double Distance2(double x1, double y1, double x2, double y2);
	void OnRun();
	//与地图相关的成员变量
	double m_nMapScale;//缩放比例
	BOOL m_bLoad;//用以表示地图文件是否已经导入

	//一些不变的参数.
	short** m_pShortFirst;//原始数据,精度最高.
	int m_nWidthFirst;//列数.
	int m_nHeightFirst;//行数.

	GridData m_gdData;//格网对象。
	short** m_ppShort;//地形原始数据。

	//地图信息
	int m_nWidth;//列数.
	int m_nHeight;//行数.
	double m_dXllcorner;//左下角点的东向坐标值.
	double m_dYllcorner;//左下角点的北向坐标值.
	double m_dCellsize;//格网距离.
	float  m_fCoordef;//坐标系统.
	float  m_fCellsize;
	short  m_nRatio;//格网大小描述比率; 
	short  m_nNodata;//物数据的表示.

	//画图控制.
	POINT m_orgBmp;//位图左上角逻辑坐标。

	// Dialog Data
	//{{AFX_DATA(CClientDlg)
	enum { IDD = IDD_CLIENT_DIALOG };
	CString	m_editPrint;
	CIPAddressCtrl	m_IpAddr;
	DWORD	m_OldIpAddr;
	UINT	m_port;
	UINT    m_OldPort;
	int		m_role;
	CString	m_mapPath;
	//}}AFX_DATA

	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CClientDlg)
public:
	virtual BOOL DestroyWindow();
protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV support
	//}}AFX_VIRTUAL

	// Implementation
protected:
	HICON m_hIcon;

	// Generated message map functions
	//{{AFX_MSG(CClientDlg)
	afx_msg VOID OnRegister();
	virtual BOOL OnInitDialog();
	afx_msg void OnSysCommand(UINT nID, LPARAM lParam);
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	afx_msg void OnServerInfoSet();
	afx_msg void OnConnectServer();
	afx_msg void OnBrowse();
	afx_msg void OnButton1();
	afx_msg void OnSelchangeRole();
	afx_msg void OnFieldchangedIpaddress1(NMHDR* pNMHDR, LRESULT* pResult);
	//}}AFX_MSG
	afx_msg LRESULT OnClientMessage(WPARAM wParam, LPARAM lParam);
	DECLARE_MESSAGE_MAP()
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_CLIENTDLG_H__DABB0C52_DA57_4B00_AA0A_DCC14F133617__INCLUDED_)
