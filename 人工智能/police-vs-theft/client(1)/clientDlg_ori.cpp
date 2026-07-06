// clientDlg.cpp : implementation file
//

#include "stdafx.h"
#include "client.h"
#include "clientDlg.h"
#include <math.h>
#include <random>
#include<iostream>
#include <fstream>
#include<ctime>
#include <cmath>
#include <stdexcept>

using namespace std;

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif


/////////////////////////////////////////////////////////////////////////////
// CAboutDlg dialog used for App About

class CAboutDlg : public CDialog
{
public:
	CAboutDlg();

	// Dialog Data
		//{{AFX_DATA(CAboutDlg)
	enum { IDD = IDD_ABOUTBOX };
	//}}AFX_DATA

	// ClassWizard generated virtual function overrides
	//{{AFX_VIRTUAL(CAboutDlg)
protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV support
	//}}AFX_VIRTUAL

// Implementation
protected:
	//{{AFX_MSG(CAboutDlg)
	//}}AFX_MSG
	DECLARE_MESSAGE_MAP()
};

CAboutDlg::CAboutDlg() : CDialog(CAboutDlg::IDD)
{
	//{{AFX_DATA_INIT(CAboutDlg)
	//}}AFX_DATA_INIT
}

void CAboutDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	//{{AFX_DATA_MAP(CAboutDlg)
	//}}AFX_DATA_MAP
}

BEGIN_MESSAGE_MAP(CAboutDlg, CDialog)
	//{{AFX_MSG_MAP(CAboutDlg)
		// No message handlers
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CClientDlg dialog

CClientDlg::CClientDlg(CWnd* pParent /*=NULL*/)
	: CDialog(CClientDlg::IDD, pParent)
{
	//{{AFX_DATA_INIT(CClientDlg)
	m_editPrint = _T("客户端启动成功！");
	m_port = 6000;
	m_OldPort = m_port;
	m_role = 0;
	register_success = false;
	m_mapPath = _T("");
	//}}AFX_DATA_INIT
	// Note that LoadIcon does not require a subsequent DestroyIcon in Win32
	m_socket = NULL;
	m_bConnect = false;
	m_bInit = false;
	s_registerRequire = false;
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);


	///地图相关初始化设置
	m_bLoad = FALSE;		//用以表示地图文件是否已经打开
	m_nMapScale = 1;		//地图的初始显示比例.

	m_ppShort = NULL;		//地形原始数据。
	m_pShortFirst = NULL;	//原始数据,精度最高
	//地图信息
	m_nWidth = 1200;		//列数.
	m_nHeight = 1200;		//行数.
	m_dXllcorner = 0;		//左下角点的东向坐标值.
	m_dYllcorner = 0;		//左下角点的北向坐标值.
	m_dCellsize = 0;		//格网距离.
	m_fCoordef = 0;		//坐标系统.
	m_fCellsize = 0;
	m_nRatio = 1;			//格网大小描述比率; 
	m_nNodata = 0;		//物数据的表示.
	//画图控制.
	m_orgBmp.x = 10;		//位图左上角逻辑坐标。
	m_orgBmp.y = 10;
	m_nWidthFirst = 1200;	//列数.
	m_nHeightFirst = 1200;//行数.

}

void CClientDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialog::DoDataExchange(pDX);
	//{{AFX_DATA_MAP(CClientDlg)
	DDX_Text(pDX, IDC_EDIT_PRINT, m_editPrint);
	DDX_Control(pDX, IDC_IPADDRESS1, m_IpAddr);
	DDX_Text(pDX, IDC_EDITPORT, m_port);
	DDV_MinMaxUInt(pDX, m_port, 1025, 65536);
	DDX_CBIndex(pDX, IDC_ROLE, m_role);
	DDX_Text(pDX, IDC_MAP_PATH, m_mapPath);
	//}}AFX_DATA_MAP
}

BEGIN_MESSAGE_MAP(CClientDlg, CDialog)
	//{{AFX_MSG_MAP(CClientDlg)
	ON_BN_CLICKED(IDC_BUTTON_REGISTER, OnRegister)
	ON_WM_SYSCOMMAND()
	ON_WM_PAINT()
	ON_WM_QUERYDRAGICON()
	ON_BN_CLICKED(IDC_BUTTON_SET, OnServerInfoSet)
	ON_BN_CLICKED(IDC_BUTTON_CONNECT, OnConnectServer)
	ON_BN_CLICKED(IDC_BUTTON_SET2, OnBrowse)
	ON_BN_CLICKED(IDC_BUTTON1, OnButton1)
	ON_CBN_SELCHANGE(IDC_ROLE, OnSelchangeRole)
	ON_NOTIFY(IPN_FIELDCHANGED, IDC_IPADDRESS1, OnFieldchangedIpaddress1)
	//}}AFX_MSG_MAP
	ON_MESSAGE(UM_ClientSOCK, OnClientMessage)
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CClientDlg message handlers

BOOL CClientDlg::OnInitDialog()
{
	CDialog::OnInitDialog();

	// Add "About..." menu item to system menu.

	// IDM_ABOUTBOX must be in the system command range.
	ASSERT((IDM_ABOUTBOX & 0xFFF0) == IDM_ABOUTBOX);
	ASSERT(IDM_ABOUTBOX < 0xF000);

	CMenu* pSysMenu = GetSystemMenu(FALSE);
	if (pSysMenu != NULL)
	{
		CString strAboutMenu;
		strAboutMenu.LoadString(IDS_ABOUTBOX);
		if (!strAboutMenu.IsEmpty())
		{
			pSysMenu->AppendMenu(MF_SEPARATOR);
			pSysMenu->AppendMenu(MF_STRING, IDM_ABOUTBOX, strAboutMenu);
		}
	}

	// Set the icon for this dialog.  The framework does this automatically
	//  when the application's main window is not a dialog
	SetIcon(m_hIcon, TRUE);			// Set big icon
	SetIcon(m_hIcon, FALSE);		// Set small icon

	// TODO: Add extra initialization here
	m_IpAddr.SetAddress(192, 168, 127, 1);
	m_IpAddr.GetAddress(m_OldIpAddr);

	((CComboBox*)GetDlgItem(IDC_ROLE))->AddString("警察");
	((CComboBox*)GetDlgItem(IDC_ROLE))->AddString("逃犯");
	((CComboBox*)GetDlgItem(IDC_ROLE))->SetCurSel(m_role);

	InitializeSocket();

	return TRUE;  // return TRUE  unless you set the focus to a control
}

void CClientDlg::OnSysCommand(UINT nID, LPARAM lParam)
{
	if ((nID & 0xFFF0) == IDM_ABOUTBOX)
	{
		CAboutDlg dlgAbout;
		dlgAbout.DoModal();
	}
	else
	{
		CDialog::OnSysCommand(nID, lParam);
	}
}

// If you add a minimize button to your dialog, you will need the code below
//  to draw the icon.  For MFC applications using the document/view model,
//  this is automatically done for you by the framework.

void CClientDlg::OnPaint()
{
	if (IsIconic())
	{
		CPaintDC dc(this); // device context for painting

		SendMessage(WM_ICONERASEBKGND, (WPARAM)dc.GetSafeHdc(), 0);

		// Center icon in client rectangle
		int cxIcon = GetSystemMetrics(SM_CXICON);
		int cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		int x = (rect.Width() - cxIcon + 1) / 2;
		int y = (rect.Height() - cyIcon + 1) / 2;

		// Draw the icon
		dc.DrawIcon(x, y, m_hIcon);
	}
	else
	{
		CDialog::OnPaint();
	}
}

// The system calls this to obtain the cursor to display while the user drags
//  the minimized window.
HCURSOR CClientDlg::OnQueryDragIcon()
{
	return (HCURSOR)m_hIcon;
}

BOOL CClientDlg::InitializeSocket()   //网络初始化
{
	if (m_bInit)
	{
		return true;
	}
	//=============================网络初始化==================================
	WORD wVersionRequested;
	WSADATA wsaData;
	int err;

	wVersionRequested = MAKEWORD(2, 0);

	err = WSAStartup(wVersionRequested, &wsaData);
	if (err != 0) {
		switch (err) {
		case WSASYSNOTREADY:
			MessageBox("错误: 网络设备没有准备好!", "Error", MB_OK | MB_ICONERROR);
			break;
		case WSAVERNOTSUPPORTED:
			MessageBox("错误: Winsock的版本信息号不支持!", "Error", MB_OK | MB_ICONERROR);
			break;
		case WSAEINPROGRESS:
			MessageBox("错误: 一个阻塞式的Winsock1.1存在于进程中!", "Error", MB_OK | MB_ICONERROR);
			break;
		case WSAEPROCLIM:
			MessageBox("错误: 已经达到Winsock使用量的上限!", "Error", MB_OK | MB_ICONERROR);
			break;
		default:
			MessageBox("错误: 套接字加载出错!", "server", MB_OK | MB_ICONERROR);
			break;
		}

		return FALSE;
	}

	if (LOBYTE(wsaData.wVersion) != 2 ||
		HIBYTE(wsaData.wVersion) != 0) {
		MessageBox("错误: 无法找到一个适用的Winsock动态链接库,需要2.2版Winsock.dll!", "server", MB_OK);
		return false;
	}

	//=========================得到主机相关信息================================

	///得到本地主机名
	int nComputerNameLen;
	nComputerNameLen = MAX_COMPUTERNAME_LENGTH + 1;
	if (SOCKET_ERROR == gethostname(client_info.c_Name, nComputerNameLen))
	{
		MessageBox("获得本地主机名出错！", "Error", MB_OK | MB_ICONERROR);
		return false;
	}

	///得到主机IP地址
	HOSTENT* pHost;
	pHost = NULL;
	if (!(pHost = gethostbyname(client_info.c_Name)))
	{
		MessageBox("获得本地主机IP地址出错！", "Error", MB_OK | MB_ICONERROR);
		return 0;
	}

	char   m_cLocalHostAddr[16];
	memcpy(&(client_info.c_IP).S_un.S_addr, pHost->h_addr, pHost->h_length);
	strcpy(m_cLocalHostAddr, inet_ntoa(client_info.c_IP));

	GetDlgItem(IDC_IPADDRESS)->SetWindowText(m_cLocalHostAddr);//将信息显示到INFO界面上
	GetDlgItem(IDC_LOCALNAME)->SetWindowText(client_info.c_Name);

	///创建套接字
	if (!CreateSocket())
	{
		m_editPrint += "\r\n网络初始化失败，重新初始化网络···";

		CEdit* scrollbar = NULL;       //随时跟踪滚动条的位置
		scrollbar = (CEdit*)GetDlgItem(IDC_EDIT_PRINT);
		scrollbar->LineScroll(scrollbar->GetLineCount());

		return false;
	}
	m_editPrint += "\r\n网络初始化成功，等待连接服务器···";

	CEdit* scrollbar = NULL;			//随时跟踪滚动条的位置
	scrollbar = (CEdit*)GetDlgItem(IDC_EDIT_PRINT);
	scrollbar->LineScroll(scrollbar->GetLineCount());

	UpdateData(false);
	m_bInit = true;
	return true;
}

void CClientDlg::OnRegister() //向服务器注册
{
	if (register_success || !m_bConnect || !m_bLoad)
		return;

	int err;
	CString c_message;

	UpdateData();

	client_info.role = m_role;
	client_info.map_name = m_strFileName;

	ToServerRegisterMessage(m_socket, &client_info);//往服务器发送注册消息
}

BOOL CClientDlg::DestroyWindow()
{
	WSAAsyncSelect(m_socket, m_hWnd, 0, 0);
	if (m_socket)
	{
		closesocket(m_socket);
	}
	WSACleanup();        //卸载套接字

	return CDialog::DestroyWindow();
}

void CClientDlg::OnServerInfoSet() //设置服务器IP地址和端口号
{
	UpdateData();
	DWORD addrIP;
	m_IpAddr.GetAddress(addrIP);
	if (m_OldPort == m_port && m_OldIpAddr == addrIP)
		return;

	if (m_socket)
	{
		closesocket(m_socket);
		m_bConnect = false;
		register_success = false;
		s_registerRequire = false;
	}

	m_IpAddr.GetAddress(m_OldIpAddr);
	m_OldPort = m_port;

	CreateSocket();

	//置连接服务器按钮使能
	GetDlgItem(IDC_BUTTON_CONNECT)->EnableWindow(TRUE);
	GetDlgItem(IDC_BUTTON_SET)->EnableWindow(FALSE);
}

BOOL CClientDlg::CreateSocket()	//创建套接字
{
	if (m_socket)     //如果已经创建套接字，就关闭以前的
	{
		WSAAsyncSelect(m_socket, m_hWnd, 0, 0);
		closesocket(m_socket);
		m_socket = NULL;
	}
	if (NULL == m_socket)
	{
		///创建新的套接字
		m_socket = socket(AF_INET, SOCK_STREAM, 0);//流类型的套接字
		if (INVALID_SOCKET == m_socket)
		{
			MessageBox("创建套接字失败！", "Error", MB_OK | MB_ICONERROR);
			return false;
		}
	}

	//注册网络事件，实现非阻塞模式
	if (SOCKET_ERROR == WSAAsyncSelect(m_socket, m_hWnd, UM_ClientSOCK, FD_READ | FD_WRITE | FD_CLOSE | FD_CONNECT))
	{
		MessageBox("注册网络事件失败！", "Error", MB_OK | MB_ICONERROR);
		return 0;
	}

	return true;
}


LRESULT CClientDlg::OnClientMessage(WPARAM wParam, LPARAM lParam)//异步通信事件响应函数
{
	char buff[1024];
	char* m_buff = NULL;
	int len, i, j;
	CString str = "服务器：";
	char temp[100];
	char s_long[14] = { '\0' };
	char s_lat[14] = { '\0' };
	char  s_eyeshot[5] = { '\0' };
	char  s_stepLength[5] = { '\0' };
	Move_position m_pos;

	switch (LOWORD(lParam))
	{
	case FD_CONNECT:
		break;

	case FD_READ:
		///接收服务器端发过来的数据
		len = recv(m_socket, buff, 1024, 0);
		if (0 == len || SOCKET_ERROR == len)
		{
			if (!s_registerRequire)
			{
				MessageBox("接受注册请求信息失败！", "Error", MB_OK | MB_ICONERROR);
				return false;
			}
			///接收数据失败
			MessageBox("接收数据失败！", "Error", MB_OK | MB_ICONWARNING);
			return 0;
		}

		switch (buff[0])
		{
		case 'r':           //连接成功消息处理
			switch (buff[1]) {
			case '1':       //连接成功
				m_bConnect = true;
				s_registerRequire = true;
				GetDlgItem(IDC_BUTTON_CONNECT)->EnableWindow(false);
				break;

			case '0':       //连接失败
				m_bInit = false;
				WSAAsyncSelect(m_socket, m_hWnd, 0, 0);
				closesocket(m_socket);
				WSACleanup();        //卸载套接字
				m_socket = NULL;
				break;

			default:
				break;
			}
			len = strlen(buff);
			m_buff = new char[len - 1];
			for (i = 0; i < len - 2; i++)
			{
				m_buff[i] = buff[i + 2];
			}
			m_buff[len - 2] = '\0';
			str = str + m_buff;
			m_editPrint = m_editPrint + "\r\n" + str;

			break;

		case 'a':            //注册应答消息处理
			switch (buff[1]) {
			case '1':         //注册成功
				register_success = true;
				m_editPrint = m_editPrint + "\r\n注册成功！";
				GetDlgItem(IDC_BUTTON_REGISTER)->EnableWindow(FALSE);//置“注册”按钮无效
				break;

			case '0':         //注册失败
				MessageBox("注册失败！", "warning", MB_OK | MB_ICONWARNING);
				len = strlen(buff);
				m_buff = new char[len - 1];
				for (i = 0; i < len - 2; i++)
				{
					m_buff[i] = buff[i + 2];
				}
				m_buff[len - 2] = '\0';
				str = str + m_buff;
				m_editPrint = m_editPrint + "\r\n" + str;
				break;
			}
			break;

		case 'd':   //每个时间步服务器发过来的数据（自身的位置数据，其它警察的位置数据）

			//////////////////////////////////////////////////////////////////////////
			str = str + buff;
			m_editPrint = m_editPrint + "\r\n\r\n" + str;//察看一下时间同步数据信息
			//////////////////////////////////////////////////////////////////////////
			client_info.c_friendPosition.RemoveAll();
			client_info.c_enemyPosition.RemoveAll();

			int t;
			for (i = 0; i < 13; i++)//读取当前位置信息
			{
				s_long[i] = buff[i + 8];
				s_lat[i] = buff[i + 21];
			}
			client_info.c_long = atof(s_long);//更新Agent信息结构体
			client_info.c_lat = atof(s_lat);
			switch (buff[7])
			{
			case '0':  //警察
				temp[0] = buff[34];
				temp[1] = buff[35];
				temp[2] = '\0';
				len = atoi(temp);//警察同行的数目

				for (i = 0; i < len; i++)
				{
					for (j = 0; j < 13; j++)//读取节点值
					{
						s_long[j] = buff[i * 26 + j + 36];
						s_lat[j] = buff[i * 26 + j + 49];
					}
					m_pos.c_long = atof(s_long);//存储其他警察同行的位置信息
					m_pos.c_lat = atof(s_lat);
					client_info.c_friendPosition.AddTail(m_pos);
				}
				t = 26 * len + 35;
				temp[0] = buff[t + 1];
				temp[1] = buff[t + 2];
				temp[2] = '\0';
				len = atoi(temp);//看到敌方的数目

				for (i = 0; i < len; i++)
				{
					for (j = 0; j < 13; j++)//读取节点值
					{
						s_long[j] = buff[i * 26 + j + t + 3];
						s_lat[j] = buff[i * 26 + j + t + 16];
					}
					m_pos.c_long = atof(s_long);//存储观测到的敌方的位置信息
					m_pos.c_lat = atof(s_lat);
					client_info.c_enemyPosition.AddTail(m_pos);
				}

				break;
			case '1':    //逃犯
				temp[0] = buff[34];
				temp[1] = buff[35];
				temp[2] = '\0';
				len = atoi(temp);//看到敌方的数目

				for (i = 0; i < len; i++)
				{
					for (j = 0; j < 13; j++)//读取节点值
					{
						s_long[j] = buff[i * 26 + j + 36];
						s_lat[j] = buff[i * 26 + j + 49];
					}
					m_pos.c_long = atof(s_long);//存储观测到的敌方的位置信息
					m_pos.c_lat = atof(s_lat);
					client_info.c_enemyPosition.AddTail(m_pos);
				}

				break;
			}
			//////////////////////////////////////////////////////////////////////////
			//相应的处理
			OnRun();

			break;

		case 's':   //接收处理游戏开始消息
			len = strlen(buff) - 35;
			m_buff = new char[len + 1];
			for (i = 0; i < len; i++)
			{
				m_buff[i] = buff[i + 35];
			}
			m_buff[len] = '\0';
			str = str + m_buff;
			m_editPrint = m_editPrint + "\r\n\r\n" + str;

			for (i = 0; i < 13; i++)
			{
				s_long[i] = buff[i + 1];
				s_lat[i] = buff[i + 14];
			}
			client_info.c_long = atof(s_long);//储存初始经纬度信息
			client_info.c_lat = atof(s_lat);

			sprintf(temp, "初始经度：%s     初始纬度：%s ", s_long, s_lat);
			m_editPrint = m_editPrint + "\r\n" + temp;

			for (i = 0; i < 4; i++)
			{
				s_eyeshot[i] = buff[i + 27];
				s_stepLength[i] = buff[i + 31];
			}
			client_info.c_eyeshot = atof(s_eyeshot);//储存视野范围，最大步长信息
			client_info.c_stepLength = atof(s_stepLength);

			sprintf(temp, "视野范围：%s      最大步长：%s ", s_eyeshot, s_stepLength);
			m_editPrint = m_editPrint + "\r\n\r\n" + temp;

			//////////////////////////////////////////////////////////////
			OnRun(); //算法开始运行

			break;

		case 'e':          //出错消息处理
			len = strlen(buff);
			m_buff = new char[len];
			for (i = 0; i < len - 1; i++)
			{
				m_buff[i] = buff[i + 1];
			}
			m_buff[len - 1] = '\0';
			str = str + m_buff;
			m_editPrint = m_editPrint + "\r\n\r\n" + str;

			break;

		case 'q':          //游戏结束消息处理
			len = strlen(buff);
			m_buff = new char[len];
			for (i = 0; i < len - 1; i++)
			{
				m_buff[i] = buff[i + 1];
			}
			m_buff[len - 1] = '\0';
			str = str + "游戏结束！\r\n" + m_buff;
			m_editPrint = m_editPrint + "\r\n\r\n" + str;
			////////////////////////////////////////////////////////////////
			//程序中止运行！

			break;

		default:
			//MessageBox("服务器端发送的消息无效或格式错误！","warning",MB_OK | MB_ICONWARNING);
			///给服务器端发送格式错误消息
			//sprintf(buff,"e消息无效或格式错误,请重发！");
			//len=strlen(buff);
			//len=send(m_socket,buff,len+1,0);
			return 0;
		}
		delete[] m_buff;
		break;

	case FD_WRITE:
		break;

	case FD_CLOSE:    //连接中断响应处理
		if (wParam == m_socket)
		{
			MessageBox("与服务器端的连接中断！", "Warning", MB_OK | MB_ICONWARNING);

			//清理相关项
			WSAAsyncSelect(m_socket, m_hWnd, 0, 0);
			closesocket(m_socket);  //释放连接资源
			m_editPrint += "\r\n请重新连接服务器···";

			m_socket = NULL;
			m_bConnect = false;
			m_bInit = false;
			s_registerRequire = false;
			register_success = false;

			GetDlgItem(IDC_BUTTON_REGISTER)->EnableWindow(FALSE);
			GetDlgItem(IDC_BUTTON_CONNECT)->EnableWindow(TRUE);

		}
		break;

	default:
		MessageBox("与服务器端的网络连接出错,网络连接中断！", "warning", MB_OK | MB_ICONWARNING);
		closesocket(m_socket);
		m_bInit = false;
		m_bConnect = false;

		m_editPrint = m_editPrint + "\r\n与服务器端的网络连接出错,网络连接中断！";

	}

	UpdateData(false);

	CEdit* scrollbar = NULL;       //随时跟踪滚动条的位置
	scrollbar = (CEdit*)GetDlgItem(IDC_EDIT_PRINT);
	scrollbar->LineScroll(scrollbar->GetLineCount());

	return 0;
}

void CClientDlg::OnConnectServer() //连接服务器
{
	if (!m_bInit)
	{
		InitializeSocket();
	}
	if (m_bConnect)
	{
		return;
	}

	///设置服务器IP地址和端口号
	UpdateData();
	severAddr.sin_family = AF_INET;
	DWORD addrIP;
	m_IpAddr.GetAddress(addrIP);
	severAddr.sin_addr.S_un.S_addr = htonl(addrIP);
	severAddr.sin_port = htons(m_port);

	///同服务器建立连接
	int ret = connect(m_socket, (SOCKADDR*)&severAddr, sizeof(SOCKADDR));

	//select 模型，即设置超时
	struct timeval timeout;
	fd_set r;
	FD_ZERO(&r);
	FD_SET(m_socket, &r);
	timeout.tv_sec = 2; //连接超时2秒
	timeout.tv_usec = 0;
	ret = select(0, 0, &r, 0, &timeout);
	if (ret > 0)
	{
		//		m_bConnect=true;
		//		
		//		CEdit* scrollbar=NULL;       //随时跟踪滚动条的位置
		//		scrollbar=(CEdit*)GetDlgItem(IDC_EDIT_PRINT);
		//		scrollbar->LineScroll(scrollbar->GetLineCount());
		// 		UpdateData(false);

		GetDlgItem(IDC_BUTTON_REGISTER)->EnableWindow(true);//置“注册”按钮生效
		return;
	}

	MessageBox("连接服务器失败！", "Warning", MB_OK | MB_ICONWARNING);
	m_editPrint += "\r\n请重新连接服务器！";
	CEdit* scrollbar = NULL;       //随时跟踪滚动条的位置
	scrollbar = (CEdit*)GetDlgItem(IDC_EDIT_PRINT);
	scrollbar->LineScroll(scrollbar->GetLineCount());
	UpdateData(false);

	return;
}

void CClientDlg::OnBrowse() //地图浏览窗口
{
	CString szFilter = "数字高程地图文件 (*.rec;*.grd)|*.rec;*.grd|所有文件 (*.*)|*.*||";
	CFileDialog dlgFile(TRUE, NULL, NULL, 0, szFilter);
	dlgFile.m_ofn.lpstrTitle = "选择地图文件";

	if (dlgFile.DoModal() == IDCANCEL)
		return;

	m_mapPath = m_strFilePath = dlgFile.GetPathName();
	m_strFileName = dlgFile.GetFileName();

	CString Suffix = GetSuffix(m_strFilePath);//得到文件后缀名
	LPTSTR pName = m_strFilePath.GetBuffer(m_strFilePath.GetLength());//得到文件名
	m_gdData.init(pName);//初始化格网对象.

	if (Suffix == "error")
	{

		if (!m_gdData.data)//如果没有数据则返回.
		{
			::AfxMessageBox("打开的地图文件格式错误!", MB_OK);
			return;
		}
		m_pShortFirst = m_gdData.data_s;			//原始数据.
		m_ppShort = m_gdData.data_s;				//把数据取出来.
		DataDescription* pDD = m_gdData.dd;
		LayerDescription* pLD = pDD->ld;
		m_nWidthFirst = m_nWidth = pDD->ncols;		//列数 =1440
		m_nHeightFirst = m_nHeight = pDD->nrows;	//行数 = 1320
		m_dXllcorner = pDD->xllcorner;			//左下角点的东向坐标值 = 109.00000000000
		m_dYllcorner = pDD->yllcorner;			//左下角点的北向坐标值 = 26.000000000000
		m_dCellsize = pDD->cellsize;				//格网距离 0.0083333333333333
		m_fCoordef = pLD->coordef;				//800表示大地经纬度坐标系统
		m_fCellsize = pLD->cellsize;				//30.0000
		m_nRatio = pLD->ratio;					//格网大小描述比率; 3600
		m_nNodata = pLD->nodata;					//无数据的表示.  0

	}
	else if (Suffix == "grd" || Suffix == "GRD")
	{
		FILE* pFile = fopen(m_strFilePath, "rt");
		int i, j;

		if (!pFile)
		{
			AfxMessageBox("地图文件打开错误！", MB_OK, 0);
			m_ppShort = NULL;
			return;
		}
		else
		{
			int nBuf;
			float fBuf;
			char nCh[20];

			fseek(pFile, 0L, SEEK_SET);
			fscanf(pFile, "%s", &nCh);
			fscanf(pFile, "%d", &nBuf);
			m_nWidthFirst = m_nWidth = nBuf;

			fscanf(pFile, "%s", &nCh);
			fscanf(pFile, "%d", &nBuf);
			m_nHeightFirst = m_nHeight = nBuf;

			fscanf(pFile, "%s", &nCh);
			fscanf(pFile, "%f", &fBuf);
			m_dXllcorner = fBuf;

			fscanf(pFile, "%s", &nCh);
			fscanf(pFile, "%f", &fBuf);
			m_dYllcorner = fBuf;

			fscanf(pFile, "%s", &nCh);
			fscanf(pFile, "%f", &fBuf);
			m_fCellsize = m_dCellsize = fBuf;

			fscanf(pFile, "%s", &nCh);
			fscanf(pFile, "%d", &nBuf);
			m_nNodata = nBuf;

			m_fCoordef = 54;
			m_nRatio = 0.3;

			m_ppShort = new short* [m_nHeight];
			for (int k = 0; k < m_nHeight; k++)
			{
				m_ppShort[k] = new short[m_nWidth];
			}



			for (i = 0; i < m_nHeight; i++)
			{
				for (j = 0; j < m_nWidth; j++)
				{

					fscanf(pFile, "%d", &nBuf);
					m_ppShort[i][j] = nBuf;

				}

			}
			fclose(pFile);

		}
	}
	else if (Suffix == "rec" || Suffix == "REC")
	{
		m_pShortFirst = m_gdData.data_s;			//原始数据.
		m_ppShort = m_gdData.data_s;				//把数据取出来.
		DataDescription* pDD = m_gdData.dd;
		LayerDescription* pLD = pDD->ld;
		m_nWidthFirst = m_nWidth = pDD->ncols;		//列数 =1440
		m_nHeightFirst = m_nHeight = pDD->nrows;	//行数 = 1320
		m_dXllcorner = pDD->xllcorner;			//左下角点的东向坐标值 = 109.00000000000
		m_dYllcorner = pDD->yllcorner;			//左下角点的北向坐标值 = 26.000000000000
		m_dCellsize = pDD->cellsize;				//格网距离 0.0083333333333333
		m_fCoordef = pLD->coordef;				//坐标系统 800.000
		m_fCellsize = pLD->cellsize;				//30.0000
		m_nRatio = pLD->ratio;					//格网大小描述比率; 3600
		m_nNodata = pLD->nodata;					//无数据的表示.  0

	}
	else
	{
		MessageBox("打开的地图文件格式错误！\n地图文件只能是*.grd和*rec文件。", "出错", MB_ICONERROR | MB_OK);
		return;
	}

	m_bLoad = TRUE;
	UpdateData(false);

}

CString CClientDlg::GetSuffix(CString PathName)//获得文件名的后缀
{
	int l = PathName.GetLength();
	CString SuffixBuffer;
	int n = 0;
	for (l; l > 0; l--)
	{
		if (PathName[l - 1] == '.')
		{
			n = PathName.GetLength() - l;
			break;
		}
	}
	if (n < 2)
		return SuffixBuffer = "error";
	for (int m = 0; m < n; m++)
		SuffixBuffer += PathName[PathName.GetLength() - n + m];
	return SuffixBuffer;
}

BOOL CClientDlg::ToServerDate(SOCKET s, MoveList* list)//往服务器发送当前时间步长内移动信息
{
	CString temp, buff;
	int err, len = list->GetCount();

	if (len > 100) //最多允许发送100个点序列
	{
		len = 100;
	}

	buff.Format("d%.3d", len);//设置消息头

	Move_position node;

	for (int i = 0; i < len; i++)
	{
		node = list->GetAt(list->FindIndex(i));
		temp.Empty();
		if ((node.c_long <= 180) && (node.c_long >= -180) && (node.c_lat <= 90) && (node.c_lat >= -90))
		{
			temp.Format("%13e%13e", node.c_long, node.c_lat);
			buff += temp;
		}
	}

	err = send(s, buff.GetBuffer(0), buff.GetLength() + 1, 0);
	if (err != buff.GetLength() + 1)
	{
		///发送位置信息失败
		MessageBox("发送位置信息失败！", "Error", MB_OK | MB_ICONWARNING);
		return false;
	}

	return true;
}

BOOL CClientDlg::ToServerRegisterMessage(SOCKET s, C_INFO* info)//往服务器发送注册消息
{
	int err;
	CString temp;
	temp.Empty();

	char len[] = { '0','0' };
	int n = strlen(info->c_Name);
	char t;
	if (n > 9)
	{
		_itoa(n, len, 10);
	}
	else
	{
		_itoa(n, &len[1], 10);
	}

	char len1[] = { '0','0' };
	int n1 = (info->map_name).GetLength();
	if (n1 > 9)
	{
		_itoa(n1, len1, 10);
	}
	else
	{
		_itoa(n1, &len1[1], 10);
	}

	temp += 'r';
	temp += char(info->role);
	temp += len[0];
	temp += len[1];
	temp += info->c_Name;
	temp += len1[0];
	temp += len1[1];
	temp += info->map_name;


	err = send(s, temp.GetBuffer(0), temp.GetLength() + 1, 0);
	if (err != temp.GetLength() + 1)
	{
		///发送注册消息失败
		register_success = false;
		MessageBox("发送注册消息失败！", "Error", MB_OK | MB_ICONWARNING);
		return false;
	}
	return true;
}



void CClientDlg::OnButton1() //测试按钮——agent位置移动example
{
	//将一个时间步内推算的移动序列存入移动序列m_moveList结构中

	//测试实例
	Move_position positon;
	m_moveList.RemoveAll();
	for (int i = 0; i < 3; i++)
	{
		positon.c_long = client_info.c_long - 0.002000;
		positon.c_lat = client_info.c_lat - 0.0020000;
		m_moveList.AddTail(positon);
	}

	ToServerDate(m_socket, &m_moveList);
}


void CClientDlg::OnSelchangeRole() //更新角色选择下列框
{
	UpdateData();
}


void CClientDlg::OnFieldchangedIpaddress1(NMHDR* pNMHDR, LRESULT* pResult) //服务器IP地址控件修改响应函数
{
	UpdateData();
	DWORD addrIP;
	m_IpAddr.GetAddress(addrIP);
	if (m_OldIpAddr == addrIP)	//修改IP地址后，只有先点击“设置”按钮后，方可点击“连接服务器”按钮
	{
		GetDlgItem(IDC_BUTTON_SET)->EnableWindow(FALSE);
		GetDlgItem(IDC_BUTTON_CONNECT)->EnableWindow(TRUE);
	}
	else
	{
		GetDlgItem(IDC_BUTTON_SET)->EnableWindow(TRUE);
		GetDlgItem(IDC_BUTTON_CONNECT)->EnableWindow(FALSE);
	}

}

double generateRandomDouble(double min, double max)
{
	// 使用默认的随机设备创建种子
	std::random_device rd;

	// 使用种子初始化梅森旋转引擎
	std::mt19937 mt(rd());

	// 创建一个均匀分布，范围为[min, max]
	std::uniform_real_distribution<double> dist(min, max);

	// 生成一个位于范围内的随机浮点数
	return dist(mt);
}


//////////////////////////////////////////////////////////////////////////
//    OnRun函数为智能体算法运行部分，请同学们自行实现！
//
//
//////////////////////////////////////////////////////////////////////////

// 计算三点形成圆的圆心
Move_position findCircleCenter(const Move_position& a, const Move_position& b, const Move_position& c)
{
	// 计算边AB和边AC的中点
	Move_position midAB{ (a.c_long + b.c_long) / 2.0, (a.c_lat + b.c_lat) / 2.0 };
	Move_position midAC{ (a.c_long + c.c_long) / 2.0, (a.c_lat + c.c_lat) / 2.0 };

	double slopeAB, slopeAC;
	bool isABVertical = std::abs(b.c_lat - a.c_lat) < 1e-6;
	bool isACVertical = std::abs(c.c_lat - a.c_lat) < 1e-6;

	// 如果AB是垂直的，斜率为0，否则计算斜率的负倒数
	if (isABVertical) {
		slopeAB = 0;
	}
	else {
		slopeAB = -(b.c_long - a.c_long) / (b.c_lat - a.c_lat);
	}

	// 如果AC是垂直的，斜率为0，否则计算斜率的负倒数
	if (isACVertical) {
		slopeAC = 0;
	}
	else {
		slopeAC = -(c.c_long - a.c_long) / (c.c_lat - a.c_lat);
	}
	std::cout << slopeAB << std::endl;
	std::cout << slopeAC << std::endl;

	// 计算垂直平分线的截距
	double kAB = midAB.c_lat - slopeAB * midAB.c_long;
	double kAC = midAC.c_lat - slopeAC * midAC.c_long;

	double centerX, centerY;

	// 如果其中一条边是垂直的，另一条不是，那么解方程的方法有所不同
	if (isABVertical && !isACVertical) {
		centerX = midAB.c_long;
		centerY = slopeAC * centerX + kAC;
	}
	else if (!isABVertical && isACVertical) {
		centerX = midAC.c_long;
		centerY = slopeAB * centerX + kAB;
	}
	else {
		// 如果两条边都不是垂直的，按照正常方法解方程
		if (std::abs(slopeAB - slopeAC) < 1e-6) {
			throw std::runtime_error("Parallel lines error: no unique intersection");
		}
		centerX = (kAC - kAB) / (slopeAB - slopeAC);
		centerY = slopeAB * centerX + kAB;
	}

	return{ centerX, centerY };
}

Move_position rotateAndMovePoint(const Move_position& point, const Move_position& center, double l_cir, double l_in) {
	// 计算原始点到圆心的极坐标
	double r = std::sqrt((point.c_long - center.c_long) * (point.c_long - center.c_long) + (point.c_lat - center.c_lat) * (point.c_lat - center.c_lat));
	double theta = std::atan2(point.c_lat - center.c_lat, point.c_long - center.c_long);

	// 计算旋转角度
	double l_rot = std::sqrt(l_cir * l_cir - l_in * l_in); // 旋转部分的长度
	double delta_theta = l_rot / r;

	// 更新后的极坐标
	double r_new = r - l_in; // 向内移动
	double theta_new = theta + delta_theta;

	// 转换回笛卡尔坐标
	double x_new = center.c_long + r_new * std::cos(theta_new);
	double y_new = center.c_lat + r_new * std::sin(theta_new);

	return{ x_new, y_new };
}

void CClientDlg::OnRun()//Agent工作进程
{
	m_moveList.RemoveAll();
	Move_position mp, mp_teammate[5], mp_enemy, mp_min_enemy, mp_enemy1, mp_enemy2;
	int friend_num = client_info.c_friendPosition.GetCount();
	int enemy_num = client_info.c_enemyPosition.GetCount();
	double stepLength = client_info.c_stepLength / 30.89 / 3600.0 * 10;
	// 获取自己当前位置
	mp.c_long = client_info.c_long;
	mp.c_lat = client_info.c_lat;

	// 获取其他同行的位置
	POSITION pos = client_info.c_friendPosition.GetHeadPosition();
	for (int i = 0; i < client_info.c_friendPosition.GetCount(); i++)
		mp_teammate[i] = (Move_position)client_info.c_friendPosition.GetNext(pos);

	// 获取所发现的对方的位置
	pos = client_info.c_enemyPosition.GetHeadPosition();
	double min_dis_enemy = 100000000.0;
	double DisFriends[2] = { 0 };
	double dis_sum = 0;
	double min_dis_sum = 100000000.0;



	for (int i = 0; i < client_info.c_enemyPosition.GetCount(); i++)
	{
		mp_enemy = (Move_position)client_info.c_enemyPosition.GetNext(pos);
		double dis = Distance2(mp.c_long, mp.c_lat, mp_enemy.c_long, mp_enemy.c_lat);

		for (int i = 0; i < client_info.c_friendPosition.GetCount(); i++) {
			DisFriends[i] = Distance2(mp_teammate[i].c_long, mp_teammate[i].c_lat, mp_enemy.c_long, mp_enemy.c_lat);
			dis_sum += DisFriends[i];
		}
		dis_sum += dis;
		/*if (dis_sum < min_dis_sum && dis_sum != 0 && i == 0) // 抓距离和最小的小偷
		{
			min_dis_sum = dis_sum;
			min_dis_enemy = dis;
			mp_min_enemy = mp_enemy;
		}
		break;*/



		if (dis < min_dis_enemy) // 抓最近的一个
		{
			min_dis_enemy = dis;
			mp_min_enemy = mp_enemy;
		}
	}

	double sin_theta = 0.0;
	double cos_theta = 0.0;
	if (client_info.role == 0) // 警察
	{
		ofstream dataFile_0;
		dataFile_0.open("dataFile_0.txt", ofstream::app);
		dataFile_0 << "I am " << client_info.role << "\n";
		dataFile_0 << "min_dis_enemy=" << min_dis_enemy << "\n";
		dataFile_0 << "mp.c_long=" << mp.c_long << " mp.c_lat=" << mp.c_lat << "\n";
		dataFile_0 << "mp_min_enemy.c_long=" << mp_min_enemy.c_long << " mp_min_enemy.c_lat=" << mp_min_enemy.c_lat << "\n";
		dataFile_0 << "init sin=" << sin_theta << " cos=" << cos_theta << "\n";
		Move_position police;
		if (enemy_num != 0)	// 如果附近有逃犯
		{
			sin_theta = (mp_min_enemy.c_lat - mp.c_lat) / min_dis_enemy;
			cos_theta = (mp_min_enemy.c_long - mp.c_long) / min_dis_enemy;
			//dis的距离最大
			if (min_dis_enemy >= DisFriends[0] && min_dis_enemy >= DisFriends[1]) {
				dataFile_0 << "yesT sin=" << sin_theta << " cos=" << cos_theta << "\n";
			}
			//同伴DisFriends[0]的距离最大
			if (DisFriends[0] >= min_dis_enemy && DisFriends[0] >= DisFriends[1]) {
				double sin_theta_friends = (mp_min_enemy.c_lat - mp_teammate[0].c_lat) / DisFriends[0];
				if (sin_theta_friends > sin_theta)
				{
					sin_theta += (sin_theta_friends * 0.5);
					if (cos_theta > 0)
					{
						cos_theta = sqrt(1 - sin_theta * sin_theta);
					}
					else
					{
						cos_theta = -sqrt(1 - sin_theta * sin_theta);
					}
				}
				else
				{
					sin_theta -= (sin_theta_friends * 0.5);
					if (cos_theta > 0)
					{
						cos_theta = sqrt(1 - sin_theta * sin_theta);
					}
					else
					{
						cos_theta = -sqrt(1 - sin_theta * sin_theta);
					}
				}
				dataFile_0 << "yesT sin=" << sin_theta << " cos=" << cos_theta << "\n";
			}
			//同伴DisFriends[1]的距离最短
			if (DisFriends[1] >= min_dis_enemy && DisFriends[1] >= DisFriends[0]) {
				double sin_theta_friends = (mp_min_enemy.c_lat - mp_teammate[1].c_lat) / DisFriends[1];
				if (sin_theta_friends > sin_theta)
				{
					sin_theta += (sin_theta_friends * 0.5);
					if (cos_theta > 0)
					{
						cos_theta = sqrt(1 - sin_theta * sin_theta);
					}
					else
					{
						cos_theta = -sqrt(1 - sin_theta * sin_theta);
					}
				}
				else
				{
					sin_theta -= (sin_theta_friends * 0.5);
					if (cos_theta > 0)
					{
						cos_theta = sqrt(1 - sin_theta * sin_theta);
					}
					else
					{
						cos_theta = -sqrt(1 - sin_theta * sin_theta);
					}
				}
				dataFile_0 << "yesT sin=" << sin_theta << " cos=" << cos_theta << "\n";
			}
			police.c_lat = mp.c_lat + sin_theta * stepLength;
			police.c_long = mp.c_long + cos_theta * stepLength;
		}
		else // 如果附近没有逃犯，就旋转向内移动
		{
			dataFile_0 << "friend_count=" << client_info.c_friendPosition.GetCount() << "\n";
			for (int i = 0; i < client_info.c_friendPosition.GetCount(); i++)
				dataFile_0 << "mp_teammate.c_long=" << mp_teammate[i].c_long << "mp_teammate.c_lat=" << mp_teammate[i].c_lat << "\n";
			if (client_info.c_friendPosition.GetCount() == 2) {
				// 计算并输出三个警察构成的圆的圆心
				Move_position police_center = findCircleCenter(mp, mp_teammate[0], mp_teammate[1]);
				dataFile_0 << "police_center.c_long=" << police_center.c_long << "mp_teammate.c_lat=" << police_center.c_lat << "\n";

				Move_position mv = rotateAndMovePoint(mp, police_center, stepLength, stepLength / 4.0);
				dataFile_0 << "mv.c_long=" << mv.c_long << "mv.c_lat=" << mv.c_lat << "\n";
				/*
				double aa = std::sqrt((mv.c_long - police_center.c_long) * (mv.c_long - police_center.c_long) + (mv.c_lat - police_center.c_lat) * (mv.c_lat - police_center.c_lat));
				std::cout << aa << std::endl;
				double bb = std::sqrt((mv.c_long - mp.c_long) * (mv.c_long - mp.c_long) + (mv.c_lat - mp.c_lat) * (mv.c_lat - mp.c_lat));
				std::cout << bb << std::endl;
				*/
				/*
				sin_theta = generateRandomDouble(-1, 1);
				cos_theta = sqrt(1 - sin_theta * sin_theta);
				if (generateRandomDouble(0, 1) < 0.5)
				cos_theta = -cos_theta;
				*/
				dataFile_0 << "noT sin=" << sin_theta << " cos=" << cos_theta << "\n";
				police.c_lat = mv.c_lat;
				police.c_long = mv.c_long;
			}
		}
		dataFile_0 << "stepLength=" << stepLength << "\n";
		dataFile_0 << "NOW sin=" << sin_theta << " cos=" << cos_theta << "\n";
		dataFile_0 << "sin_theta * stepLength=" << sin_theta * stepLength << " cos_theta * stepLength=" << cos_theta * stepLength << "\n";
		dataFile_0 << "c_long=" << police.c_long << " c_lat=" << police.c_lat << endl;
		m_moveList.AddTail(police);
		ToServerDate(m_socket, &m_moveList);
		dataFile_0.close();
	}
	else // 小偷
	{
		ofstream dataFile_1;
		dataFile_1.open("dataFile_1.txt", ofstream::app);
		dataFile_1 << "I am " << client_info.role << "\n";
		dataFile_1 << "min_dis_enemy=" << min_dis_enemy << "\n";
		dataFile_1 << "mp.c_long=" << mp.c_long << " mp.c_lat=" << mp.c_lat << "\n";
		dataFile_1 << "mp_min_enemy.c_long=" << mp_min_enemy.c_long << " mp_min_enemy.c_lat=" << mp_min_enemy.c_lat << "\n";
		Move_position thief;
		double xdis = mp.c_long - m_dXllcorner;
		double ydis = mp.c_lat - m_dYllcorner;
		double xdis_rightup = m_dXllcorner + m_nWidth * m_dCellsize - mp.c_long;
		double ydis_rightup = m_dYllcorner + m_nHeight * m_dCellsize - mp.c_lat;
		if (enemy_num == 0) { // 如果附近没有警察，就向最近地图边缘移动
			if (xdis <= xdis_rightup && ydis <= ydis_rightup) // 左下角
			{
				if (xdis <= ydis) //左
				{
					sin_theta = 0.0;
					cos_theta = -1.0;
				}
				else
				{
					sin_theta = -1.0;
					cos_theta = 0.0;
				}
			}
			else if (xdis <= xdis_rightup && ydis > ydis_rightup) // 左上角
			{
				if (xdis <= ydis_rightup) //左
				{
					sin_theta = 0.0;
					cos_theta = -1.0;
				}
				else
				{
					sin_theta = 1.0;
					cos_theta = 0.0;
				}
			}
			else if (xdis > xdis_rightup && ydis <= ydis_rightup) // 右下角
			{
				if (xdis_rightup <= ydis) //右
				{
					sin_theta = 0.0;
					cos_theta = 1.0;
				}
				else
				{
					sin_theta = -1.0;
					cos_theta = 0.0;
				}
			}
			else // 右上角
			{
				if (xdis_rightup <= ydis_rightup) //右
				{
					sin_theta = 0.0;
					cos_theta = 1.0;
				}
				else
				{
					sin_theta = 1.0;
					cos_theta = 0.0;
				}
			}
			dataFile_1 << "noP sin=" << sin_theta << " cos=" << cos_theta << "\n";
		}
		else if (enemy_num == 1) { // 如果发现1个警察，就向其反方向移动
			double sin_theta1, cos_theta1, sin_theta2, cos_theta2;
			sin_theta1 = -(mp_min_enemy.c_lat - mp.c_lat) / min_dis_enemy;
			cos_theta1 = -(mp_min_enemy.c_long - mp.c_long) / min_dis_enemy;
			dataFile_1 << "yesP sin=" << sin_theta << " cos=" << cos_theta << "\n";

			if (xdis <= xdis_rightup && ydis <= ydis_rightup) // 左下角
			{
				if (xdis <= ydis) //左
				{
					sin_theta2 = 0.0;
					cos_theta2 = -1.0;
				}
				else
				{
					sin_theta2 = -1.0;
					cos_theta2 = 0.0;
				}
			}
			else if (xdis <= xdis_rightup && ydis > ydis_rightup) // 左上角
			{
				if (xdis <= ydis_rightup) //左
				{
					sin_theta2 = 0.0;
					cos_theta2 = -1.0;
				}
				else
				{
					sin_theta2 = 1.0;
					cos_theta2 = 0.0;
				}
			}
			else if (xdis > xdis_rightup && ydis <= ydis_rightup) // 右下角
			{
				if (xdis_rightup <= ydis) //右
				{
					sin_theta2 = 0.0;
					cos_theta2 = 1.0;
				}
				else
				{
					sin_theta2 = -1.0;
					cos_theta2 = 0.0;
				}
			}
			else // 右上角
			{
				if (xdis_rightup <= ydis_rightup) //右
				{
					sin_theta2 = 0.0;
					cos_theta2 = 1.0;
				}
				else
				{
					sin_theta2 = 1.0;
					cos_theta2 = 0.0;
				}
			}

			sin_theta = sqrt((1 - cos_theta1*cos_theta2 + sin_theta1*sin_theta2) / 2);
			cos_theta = sqrt(1 - (sin_theta*sin_theta));
			if (sin_theta1 + sin_theta2 < 0)
				sin_theta = -1 * sin_theta;
			if (cos_theta1 + cos_theta2 < 0)
				cos_theta = -1 * cos_theta;
		}
		else if (enemy_num == 2) { // 如果发现2个警察，就向警察连线的中垂线背离方向移动
			POSITION pos = client_info.c_enemyPosition.GetHeadPosition();
			Move_position mp_enemy1 = (Move_position)client_info.c_enemyPosition.GetNext(pos);
			Move_position mp_enemy2 = (Move_position)client_info.c_enemyPosition.GetNext(pos);
			double mid_lat = (mp_enemy1.c_lat + mp_enemy2.c_lat) / 2.0;
			double mid_long = (mp_enemy1.c_long + mp_enemy2.c_long) / 2.0;
			double tf2mid_lat = mid_lat - mp.c_lat;
			double tf2mid_long = mid_long - mp.c_long;
			double length = sqrt(tf2mid_lat * tf2mid_lat + tf2mid_long * tf2mid_long);
			sin_theta = -tf2mid_lat / length;
			cos_theta = -tf2mid_long / length;
		}
		else if (enemy_num == 3) { // 如果发现3个警察，就向最近警察连线的中垂线背离方向移动
			POSITION pos = client_info.c_enemyPosition.GetHeadPosition();
			Move_position mp_enemy1 = (Move_position)client_info.c_enemyPosition.GetNext(pos);
			Move_position mp_enemy2 = (Move_position)client_info.c_enemyPosition.GetNext(pos);
			Move_position mp_enemy3 = (Move_position)client_info.c_enemyPosition.GetNext(pos);
			double dis1 = Distance2(mp.c_long, mp.c_lat, mp_enemy1.c_long, mp_enemy1.c_lat);
			double dis2 = Distance2(mp.c_long, mp.c_lat, mp_enemy2.c_long, mp_enemy2.c_lat);
			double dis3 = Distance2(mp.c_long, mp.c_lat, mp_enemy3.c_long, mp_enemy3.c_lat);
			double mid_lat = 0.0, mid_long = 0.0;
			if (dis1 < dis2) {
				if (dis2 < dis3) {
					// dis1 < dis2 < dis3
					mid_lat = (mp_enemy1.c_lat + mp_enemy3.c_lat) / 2.0;
					mid_long = (mp_enemy1.c_long + mp_enemy3.c_long) / 2.0;
				}
				else {
					if (dis1 < dis3) {
						// dis1 < dis3 < dis2
						mid_lat = (mp_enemy1.c_lat + mp_enemy2.c_lat) / 2.0;
						mid_long = (mp_enemy1.c_long + mp_enemy2.c_long) / 2.0;
					}
					else {
						// dis3 <= dis1 < dis2
						mid_lat = (mp_enemy3.c_lat + mp_enemy2.c_lat) / 2.0;
						mid_long = (mp_enemy3.c_long + mp_enemy2.c_long) / 2.0;
					}
				}
			}
			else {
				if (dis1 < dis3) {
					// dis2 <= dis1 < dis3
					mid_lat = (mp_enemy2.c_lat + mp_enemy3.c_lat) / 2.0;
					mid_long = (mp_enemy2.c_long + mp_enemy3.c_long) / 2.0;
				}
				else {
					if (dis2 < dis3) {
						// dis2 < dis3 < dis1
						mid_lat = (mp_enemy2.c_lat + mp_enemy1.c_lat) / 2.0;
						mid_long = (mp_enemy2.c_long + mp_enemy1.c_long) / 2.0;
					}
					else {
						// dis3 <= dis2 < dis1
						mid_lat = (mp_enemy3.c_lat + mp_enemy1.c_lat) / 2.0;
						mid_long = (mp_enemy3.c_long + mp_enemy1.c_long) / 2.0;
					}
				}
			}
			double tf2mid_lat = mid_lat - mp.c_lat;
			double tf2mid_long = mid_long - mp.c_long;
			double length = sqrt(tf2mid_lat * tf2mid_lat + tf2mid_long * tf2mid_long);
			sin_theta = -tf2mid_lat / length;
			cos_theta = -tf2mid_long / length;
		}
		thief.c_long = mp.c_long + cos_theta * stepLength;
		thief.c_lat = mp.c_lat + sin_theta * stepLength;
		dataFile_1 << "stepLength=" << stepLength << "\n";
		dataFile_1 << "NOW sin=" << sin_theta << " cos=" << cos_theta << "\n";
		dataFile_1 << "sin_theta * stepLength=" << sin_theta * stepLength << " cos_theta * stepLength=" << cos_theta * stepLength << "\n";
		dataFile_1 << "c_long=" << thief.c_long << " c_lat=" << thief.c_lat << endl;
		m_moveList.AddTail(thief);
		ToServerDate(m_socket, &m_moveList);
		dataFile_1.close();
	}
	return;
}

//计算平面距离(函数参数为经纬度坐标，输出单位为米)
double CClientDlg::Distance(double x1, double y1, double x2, double y2)
{
	return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2)) * 30.89 * 3600.0;
}

double CClientDlg::Distance2(double x1, double y1, double x2, double y2)
{
	return sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2));
}

//计算三维空间距离(函数参数为经纬度坐标，输出单位为米)
double CClientDlg::Distance3(double x1, double y1, double h1, double x2, double y2, double h2)
{
	return sqrt((pow(x1 - x2, 2) + pow(y1 - y2, 2)) * (30.89 * 3600.0 * 30.89 * 3600.0) + pow(h1 - h2, 2));
}

