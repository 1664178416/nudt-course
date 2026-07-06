
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
// 在 clientDlg.cpp 中
namespace {
	static bool IsValidFloat(double x) {
		// 检查 NaN
		if (x != x) return false;
		// 检查 Inf
		if (x > 1e308 || x < -1e308) return false;
		// 检查是否在合理范围内
		if (x < -200 || x > 200) return false;  // 经纬度合理范围
		return true;
	}
}

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
	m_IpAddr.SetAddress(10, 128, 17, 210);
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

		// 【修复】手动添加字符串结束符，防止缓冲区越界
		if (len < 1024) buff[len] = '\0';
		else buff[1023] = '\0';

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
// 辅助函数：检查数字是否有效
bool IsValidNumber(double x) {
	// 检查是否为 NaN (Not a Number) 或 无穷大
	return (x == x) && (x > -1.7976931348623158e+308 && x < 1.7976931348623158e+308);
}

BOOL CClientDlg::ToServerDate(SOCKET s, MoveList* list)
{
	CString buff;
	int len = list->GetCount();
	if (len > 100) len = 100;

	// 头部
	buff.Format("d%.3d", len);

	Move_position node;
	for (int i = 0; i < len; i++)
	{
		POSITION pos = list->FindIndex(i);
		if (pos == NULL) continue;
		node = list->GetAt(pos);

		// 【关键修复】彻底验证并清理数据
		double send_long = node.c_long;
		double send_lat = node.c_lat;

		// 1. 检查浮点数有效性（使用现有的IsValidNumber函数）
		if (!IsValidNumber(send_long)) send_long = client_info.c_long;
		if (!IsValidNumber(send_lat)) send_lat = client_info.c_lat;

		// 2. 检查范围（经纬度合理范围）
		if (send_long < -180 || send_long > 180) send_long = client_info.c_long;
		if (send_lat < -90 || send_lat > 90) send_lat = client_info.c_lat;

		// 3. 使用安全格式化
		CString temp;
		temp.Format("%13.6e%13.6e", send_long, send_lat);
		buff += temp;
	}

	// 发送前再次检查缓冲区长度
	if (buff.GetLength() > 0) {
		// 确保不超过1024字节（你的缓冲区大小）
		if (buff.GetLength() + 1 > 1024) {
			buff = buff.Left(1023);
		}

		int err = send(s, buff.GetBuffer(0), buff.GetLength() + 1, 0);
		buff.ReleaseBuffer();

		if (err == SOCKET_ERROR) {
			return FALSE;
		}
	}
	return TRUE;
}

// 原始代码：
// char len[] = { '0','0' }; 
// ...
// char len1[] = { '0','0' };

BOOL CClientDlg::ToServerRegisterMessage(SOCKET s, C_INFO* info)
{
	// 1. 准备数据
	CString sendName = info->c_Name;

	// 【关键修复点 1】必须强制截断为 10，防止服务器内存溢出崩溃
	if (sendName.GetLength() > 10)
		sendName = sendName.Left(10);

	CString sendMap = info->map_name;
	// 地图名同理，也建议限制一下
	if (sendMap.GetLength() > 10)
		sendMap = sendMap.Left(10);

	char buffer[1024];
	int p = 0; // 当前写入位置指针

	// (1) 头部 'r'
	buffer[p++] = 'r';

	// (2) 角色 
	// 【关键修复点 2】发送原始二进制数据，不要加 '0'
	buffer[p++] = (char)info->role;

	// (3) 名字长度
	int nName = sendName.GetLength();
	buffer[p++] = (nName / 10) + '0'; // 十位
	buffer[p++] = (nName % 10) + '0'; // 个位

	// (4) 名字内容
	if (nName > 0) {
		memcpy(&buffer[p], (LPCTSTR)sendName, nName);
		p += nName;
	}

	// (5) 地图长度
	int nMap = sendMap.GetLength();
	buffer[p++] = (nMap / 10) + '0';
	buffer[p++] = (nMap % 10) + '0';

	// (6) 地图内容
	if (nMap > 0) {
		memcpy(&buffer[p], (LPCTSTR)sendMap, nMap);
		p += nMap;
	}

	// (7) 结尾
	buffer[p++] = '\0';

	// 4. 发送
	int err = send(s, buffer, p, 0);

	if (err != p)
	{
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

// 【最终修复版】OnRun 函数
// 包含：
// 1. 警察逻辑：向量合成法 (彻底解决 sin_theta > 1 的数学崩溃)
// 2. 小偷逻辑：势场突围法 (保留你想要的冲向边界逻辑)
// 3. 安全补丁：数组扩容、NaN检查、除零保护
// 在 clientDlg.cpp 中

void CClientDlg::OnRun()
{
	// === 调试日志设置 ===
	static int callCount = 0;
	callCount++;
	ofstream debugLog;
	debugLog.open("debug_log.txt", ios::app); // 追加模式写入

	// 获取当前自身位置
	double current_long = client_info.c_long;
	double current_lat = client_info.c_lat;

	// 记录本轮日志
	debugLog << "=== OnRun Call #" << callCount << " ===" << endl;
	debugLog << "Role: " << (client_info.role == 0 ? "Police" : "Thief") << endl;

	try {
		// 1. 清空发送队列
		m_moveList.RemoveAll();

		// 2. 初始化基础变量
		Move_position mp; // 自身位置
		mp.c_long = current_long;
		mp.c_lat = current_lat;

		Move_position mp_teammate[100]; // 队友列表
		Move_position mp_enemy;         // 临时敌人变量
		Move_position mp_min_enemy = { 0, 0 }; // 最近的敌人

		// 获取视野范围内的数量
		int friend_num = client_info.c_friendPosition.GetCount();
		int enemy_num = client_info.c_enemyPosition.GetCount();

		// 步长计算 (保留原始公式)
		double stepLength = client_info.c_stepLength / 30.89 / 3600.0 * 10;

		// 读取队友位置
		POSITION pos = client_info.c_friendPosition.GetHeadPosition();
		for (int i = 0; i < friend_num && i < 100; i++) {
			if (pos != NULL)
				mp_teammate[i] = (Move_position)client_info.c_friendPosition.GetNext(pos);
		}

		// 读取敌人并找到最近的一个（主要用于警察追踪）
		pos = client_info.c_enemyPosition.GetHeadPosition();
		double min_dis_enemy = 1e12; // 初始设为一个很大的数

		for (int i = 0; i < enemy_num; i++) {
			if (pos == NULL) break;
			Move_position temp_enemy = (Move_position)client_info.c_enemyPosition.GetNext(pos);

			double dis = Distance2(mp.c_long, mp.c_lat, temp_enemy.c_long, temp_enemy.c_lat);
			if (dis < min_dis_enemy) {
				min_dis_enemy = dis;
				mp_min_enemy = temp_enemy;
			}
		}

		// 移动向量 (cos, sin)
		double cos_theta = 0.0;
		double sin_theta = 0.0;

		// =========================================================================
		// 👮 警察逻辑 (Role == 0) - 追捕与包抄
		// =========================================================================
		if (client_info.role == 0)
		{
			Move_position police_next;

			// --- 情况 A: 发现小偷，全力追捕 ---
			if (enemy_num != 0)
			{
				// 1. 追捕向量：指向最近的小偷
				double target_dx = mp_min_enemy.c_long - mp.c_long;
				double target_dy = mp_min_enemy.c_lat - mp.c_lat;
				double dist_target = sqrt(target_dx * target_dx + target_dy * target_dy);
				if (dist_target < 1e-6) dist_target = 1e-6; // 防止除零

				double dir_x = target_dx / dist_target;
				double dir_y = target_dy / dist_target;

				// 2. 协同向量：如果有队友，稍微远离队友，形成包围网
				if (friend_num >= 1)
				{
					double mate_dx = mp.c_long - mp_teammate[0].c_long;
					double mate_dy = mp.c_lat - mp_teammate[0].c_lat;
					double dist_mate = sqrt(mate_dx * mate_dx + mate_dy * mate_dy);

					if (dist_mate > 1e-6) {
						// 增加斥力权重 (0.4)，避免大家挤在一起抓人
						dir_x += (mate_dx / dist_mate) * 0.4;
						dir_y += (mate_dy / dist_mate) * 0.4;
					}
				}

				// 3. 归一化最终方向
				double total_len = sqrt(dir_x * dir_x + dir_y * dir_y);
				if (total_len > 1e-6) {
					cos_theta = dir_x / total_len;
					sin_theta = dir_y / total_len;
				}
			}
			// --- 情况 B: 没发现小偷，随机巡逻 ---
			else
			{
				// 向地图中心移动一点点，防止一直在边缘发呆
				double center_x = m_dXllcorner + (m_nWidth * m_dCellsize) / 2.0;
				double center_y = m_dYllcorner + (m_nHeight * m_dCellsize) / 2.0;

				double vec_x = center_x - mp.c_long;
				double vec_y = center_y - mp.c_lat;

				// 加上巨大的随机扰动，模拟四处搜寻
				double rand_angle = generateRandomDouble(0, 6.28);
				double rand_mag = sqrt(vec_x * vec_x + vec_y * vec_y); // 扰动幅度

				vec_x += cos(rand_angle) * rand_mag * 2.0;
				vec_y += sin(rand_angle) * rand_mag * 2.0;

				double len = sqrt(vec_x * vec_x + vec_y * vec_y);
				if (len > 1e-6) {
					cos_theta = vec_x / len;
					sin_theta = vec_y / len;
				}
				else {
					cos_theta = 1.0; // 默认向右
				}
			}

			// 计算下一步位置
			police_next.c_long = mp.c_long + cos_theta * stepLength;
			police_next.c_lat = mp.c_lat + sin_theta * stepLength;

			// 存入列表（等待边界检查）
			m_moveList.AddTail(police_next);
		}
		// =========================================================================
		// 🏃 小偷逻辑 (Role == 1) - 智能突围 (Cost-based Escape)
		// =========================================================================
		else
		{
			Move_position thief_next;

			// 地图边界定义
			double map_min_x = m_dXllcorner;
			double map_max_x = m_dXllcorner + m_nWidth * m_dCellsize;
			double map_min_y = m_dYllcorner;
			double map_max_y = m_dYllcorner + m_nHeight * m_dCellsize;

			// 1. 基础力：所有警察产生的斥力
			double force_x = 0.0;
			double force_y = 0.0;

			// 遍历所有可见警察
			POSITION ePos = client_info.c_enemyPosition.GetHeadPosition();
			// 我们需要把敌人位置存下来，供后面计算路权使用
			CList<Move_position, Move_position&> enemyListCache;

			for (int k = 0; k < enemy_num; k++)
			{
				if (ePos == NULL) break;
				Move_position ep = (Move_position)client_info.c_enemyPosition.GetNext(ePos);
				enemyListCache.AddTail(ep); // 缓存以便复用

				double dx = mp.c_long - ep.c_long;
				double dy = mp.c_lat - ep.c_lat;
				double dist_sq = dx * dx + dy * dy;
				double dist = sqrt(dist_sq);
				if (dist < 1e-6) dist = 1e-6;

				// 斥力模型：避免1/d^3过小，使用 1/d 
				double repulsion = 5.0 / dist;
				force_x += (dx / dist) * repulsion;
				force_y += (dy / dist) * repulsion;
			}

			// 2. 智能逃逸方向选择 (Cost Function)
			// 计算到达四个边界的物理距离
			double dist_left = abs(mp.c_long - map_min_x);
			double dist_right = abs(map_max_x - mp.c_long);
			double dist_bottom = abs(mp.c_lat - map_min_y);
			double dist_top = abs(map_max_y - mp.c_lat);

			// 初始化代价为物理距离
			double cost_left = dist_left;
			double cost_right = dist_right;
			double cost_bottom = dist_bottom;
			double cost_top = dist_top;

			// 如果有敌人挡在去往某个边界的路上，大幅增加该方向的代价
			POSITION cachePos = enemyListCache.GetHeadPosition();
			for (int k = 0; k < enemyListCache.GetCount(); k++)
			{
				Move_position ep = enemyListCache.GetNext(cachePos);
				double dx = ep.c_long - mp.c_long; // 敌人在我的相对x
				double dy = ep.c_lat - mp.c_lat;   // 敌人在我的相对y
				double dist = sqrt(dx * dx + dy * dy);
				if (dist < 1e-6) dist = 1e-6;

				// 威胁系数：敌人越近，威胁越大
				double threat = 3000.0 * (1.0 / dist);

				// 简单的象限判断：如果在左侧，则去左边的代价增加
				if (dx < 0) cost_left += threat; // 敌人在左
				if (dx > 0) cost_right += threat; // 敌人在右
				if (dy < 0) cost_bottom += threat; // 敌人在下
				if (dy > 0) cost_top += threat; // 敌人在上
			}

			// 3. 选择代价最小（最安全且最近）的方向
			double min_cost = min(min(cost_left, cost_right), min(cost_bottom, cost_top));

			// 施加逃逸引力 (Escape Force)
			double escape_force = 4000.0; // 引力要足够大，能抵消掉远处警察的微弱斥力

			if (min_cost == cost_left)        force_x -= escape_force;
			else if (min_cost == cost_right)  force_x += escape_force;
			else if (min_cost == cost_bottom) force_y -= escape_force;
			else if (min_cost == cost_top)    force_y += escape_force;

			// 4. 合成最终向量并归一化
			double total_force = sqrt(force_x * force_x + force_y * force_y);
			if (total_force > 1e-6) {
				cos_theta = force_x / total_force;
				sin_theta = force_y / total_force;
			}
			else {
				// 极端情况：合力为0（极少见），随便跑
				cos_theta = 1.0; sin_theta = 0.0;
			}

			// 计算下一步
			thief_next.c_long = mp.c_long + cos_theta * stepLength;
			thief_next.c_lat = mp.c_lat + sin_theta * stepLength;

			m_moveList.AddTail(thief_next);
		}

		// =========================================================================
		// 🌍 公共逻辑：边界强制限制 (Clamping) 与 数据有效性检查
		// =========================================================================

		// 取出刚刚计算好的位置（因为m_moveList里只有一个点）
		if (!m_moveList.IsEmpty())
		{
			Move_position& final_pos = m_moveList.GetTail();

			// 1. 地图边界限制
			double map_min_x = m_dXllcorner;
			double map_max_x = m_dXllcorner + m_nWidth * m_dCellsize;
			double map_min_y = m_dYllcorner;
			double map_max_y = m_dYllcorner + m_nHeight * m_dCellsize;

			if (final_pos.c_long < map_min_x) final_pos.c_long = map_min_x;
			if (final_pos.c_long > map_max_x) final_pos.c_long = map_max_x;
			if (final_pos.c_lat < map_min_y)  final_pos.c_lat = map_min_y;
			if (final_pos.c_lat > map_max_y)  final_pos.c_lat = map_max_y;

			// 2. NaN (非数字) 检查 - 防止程序崩溃
			if (!IsValidFloat(final_pos.c_long) || !IsValidFloat(final_pos.c_lat)) {
				debugLog << "CRITICAL ERROR: NaN detected! Resetting to current pos." << endl;
				final_pos.c_long = current_long;
				final_pos.c_lat = current_lat;
			}

			debugLog << "Sending Pos: " << final_pos.c_long << ", " << final_pos.c_lat << endl;
		}

		// 发送数据给服务器
		ToServerDate(m_socket, &m_moveList);

	}
	catch (...)
	{
		debugLog << "EXCEPTION CAUGHT in OnRun!" << endl;
		// 发生严重错误时，发送当前位置作为保底，防止掉线
		m_moveList.RemoveAll();
		Move_position safe;
		safe.c_long = current_long;
		safe.c_lat = current_lat;
		m_moveList.AddTail(safe);
		ToServerDate(m_socket, &m_moveList);
	}

	debugLog.close();
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