import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.GradientPaint;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.RenderingHints;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.sql.Date;
import java.text.DateFormat;
import java.text.Format;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.GregorianCalendar;
import java.util.StringTokenizer;

import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTabbedPane;
import javax.swing.JTable;
import javax.swing.JTextField;
import javax.swing.border.EmptyBorder;


public class MainGUI {

//Declarations

public static final File SettingsFile = new File("settings" + LoginGUI.username + ".csv");

Object[] columnNames = {"Date","Payee","Amount","Type","Balance"};

public static int lineNumber = 0;
public static double WspForecast;
public static double WspSpentCashFlow;
public static double WspIncomeCashFlow;
public static double WspBudgetCashFlow;
public static double MspSpentCashFlow;
public static double MspIncomeCashFlow;
public static double MspBudgetCashFlow;
int tokenNumber = 0;
public static String[][] settings = new String[1][2];
public static String[][] data = new String[lineNumber][5];
//GUI Declarations

JLabel BLbl = new JLabel();
JLabel XLbl = new JLabel("Budget Left");
JLabel bLeft = new JLabel("Hey there");


JButton NameAccount = new JButton();
JButton test = new JButton("test");


public static JLabel Amount = new JLabel("Hey There");
public static double balance = 0;
double budget = 0;
JTabbedPane Mainpane = new JTabbedPane();

JMenuBar menubar = new JMenuBar();
JMenu File = new JMenu("File");
JMenuItem NewTransaction = new JMenuItem("Add a new Transaction");
JMenuItem Exit = new JMenuItem("Exit");

JFrame mainframe = new JFrame("Budget Buddy 0.2");

JPanel jp1 = new JPanel();
JPanel jp2 = new JPanel();
JPanel jp3 = new JPanel();
JPanel jpN = new JPanel();
JPanel BlankPanel = new JPanel();

JPanel jpNW = new JPanel(new GridBagLayout());
JPanel jpSW = new JPanel(new BorderLayout());


Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();
//Forecast Pane
JLabel Blanklabel = new JLabel("HELLO");
JLabel MonthForecast = new JLabel("Monthly Forecast");
JLabel MonthIncome = new JLabel("Income: ");
JLabel MonthIncomeBalnce = new JLabel();
JLabel MonthSpent = new JLabel("Spent: ");
JLabel MonthBudget = new JLabel("Budget: ");
JLabel CMonthIncomeForecast = new JLabel();
JLabel CMonthSpentForecast = new JLabel();
JLabel CMonthBudgetForecast = new JLabel();
JLabel WeekForecast = new JLabel("Weekly Forecast");
JLabel WeekIncome = new JLabel("Income: ");
JLabel WeekSpent = new JLabel("Spent: ");
JLabel WeekBudget = new JLabel("Budget: ");
JLabel CWeekIncomeForecast = new JLabel("test");
JLabel CWeekSpentForecast = new JLabel("test");
JLabel CWeekBudgetForecast = new JLabel("test");
JLabel YearForecast = new JLabel("Yearly Forecast");
JLabel YearIncome = new JLabel("Income: ");
JLabel YearSpent = new JLabel("Spent: ");
JLabel YearBudget = new JLabel("Budget: ");
JLabel CYearIncomeForecast = new JLabel();
JLabel CYearSpentForecast = new JLabel();
JLabel CYearBudgetForecast = new JLabel();
JLabel CustomForecast = new JLabel("Custom Forecast");
JLabel WeeklyCashflow = new JLabel("Weekly Cash Flow");
JLabel WeeklyIncomeCashflow = new JLabel();
JLabel WeeklySpentCashflow = new JLabel();
JLabel WeeklyBudgetCashflow = new JLabel();
JLabel MonthlyCashflow = new JLabel("Monthly Cash Flow");
JLabel MonthlyIncomeCashflow = new JLabel();
JLabel MonthlySpentCashflow = new JLabel();
JLabel MonthlyBudgetCashflow = new JLabel();
JLabel YearlyCashflow = new JLabel("Yearly Cash Flow");
JLabel YearlyIncomeCashflow = new JLabel();
JLabel YearlySpentCashflow = new JLabel();
JLabel YearlyBudgetCashflow = new JLabel();


JTextField CashFlowTextField = new JTextField();
JButton CashFlowSearchButton = new JButton("Search");

double firstbudget;
public static File f = new File("Transaction" + LoginGUI.username + ".csv");
public String f1 = "Transaction" + LoginGUI.username + ".csv";

public static boolean newuser = false;

public void rmain() throws IOException {
	System.out.println("Welcome" + " " + LoginGUI.username);
	checkfile();
	System.out.println("Check user == " + checkfirstuser());

	if(checkfirstuser() == true){
		Newuser nu = new Newuser();

		nu.nusermain();	//if new user then enter new details
	}



}
public void maincalls() throws IOException{
	countlengthf(); // gets the length of the transaction and stores it in an array
	createMainGUI(); // Creates the Main GUI
	ALMainGUI(); // Calls the Action listeners for the main GUI.
}
public double getbudget() {
	BufferedReader out = null;
	try {
		out = new BufferedReader(new FileReader(SettingsFile));
	} catch (FileNotFoundException e) {
		// TODO Auto-generated catch block
		e.printStackTrace();
	}
	String strLine = null;

	int row = 0;
	int col = 0;

	try {
		while((strLine = out.readLine()) != null)
		    {
		    StringTokenizer st = new StringTokenizer(strLine,",");
		    while (st.hasMoreTokens())
		    {
		        //get next token and store it in the array
		        settings[row][col] = st.nextToken();
		        col++;


		    }

		    col = 0;
		    row++;
		    }
	} catch (IOException e) {
		// TODO Auto-generated catch block
		e.printStackTrace();
	}
	firstbudget = Double.parseDouble(settings[0][1]);
	System.out.println(firstbudget);
	return firstbudget; 
	
}
public double newbudget(){
	budget = budget + getbudget();
	for(int i = 1; i < lineNumber; i++){

		if(data[i][3].equals("Withdraw")){
			budget = budget - Double.parseDouble(data[i][2]);
			System.out.println("Withdraw");
		}if(data[i][3].equals("Deposit")){
			budget = budget + Double.parseDouble(data[i][2]);
			System.out.println("Deposit");
		}
	}
	bLeft.setText(Double.toString(budget));
	return budget;

}
public double newbalance(){
balance = 0;
	for(int i = 0; i < lineNumber; i++){

		if(data[i][3].equals("Withdraw")){
			balance = balance - Double.parseDouble(data[i][2]);
			System.out.println("Withdraw");
		}
		if(data[i][3].equals("Deposit")){
				balance = Double.parseDouble(data[i][2]) + balance;
				System.out.println("Deposit");
		}
	}
	System.out.println(balance);
	Amount.setText(Double.toString(balance));
	return balance;
}
public void checkfile() throws IOException{
	 System.out.println(newuser);
	 if(!f.exists()){
		 newuser = true;
   	  try {
   		    f.createNewFile();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
   	  System.out.println("New file " + f + " has been created to the current directory");
   	  } else {
   		maincalls();
   	  }
	 System.out.println(newuser);
}
public static Boolean checkfirstuser(){
		return newuser;
}




public void ALMainGUI(){

	NewTransaction.addActionListener(new ActionListener() {
        public void actionPerformed(ActionEvent event) {
        	mainframe.setVisible(false);
        	NewTransactionGUI Nt = new NewTransactionGUI();
        	Nt.NTGM();

        }
    });

	Exit.addActionListener(new ActionListener() {
        public void actionPerformed(ActionEvent event) {
        	newbalance();


        }
    });

}
public void countlengthf() throws IOException{

	lineNumber = 0;


    try {
		BufferedReader out = new BufferedReader(new FileReader(f));
		String strLine = null;
		StringTokenizer st = null;
		GridBagConstraints c = new GridBagConstraints();

	  	c.insets = new Insets(10,10,10,10);

		while( (f1 = out.readLine()) != null )
		{

			lineNumber++;
			//break comma separated line using ","
			st = new StringTokenizer(f1, ",");

		while(st.hasMoreTokens())
			{
				//display csv values
				tokenNumber++;
				System.out.println("Line # " + lineNumber +
						", Token # " + tokenNumber
						+ ", Token : "+ st.nextToken());

			}


			//reset token number
			tokenNumber = 0;

		}



	} catch (FileNotFoundException e) {
		// TODO Auto-generated catch block
		e.printStackTrace();
	}
    data = new String[lineNumber][5];
	System.out.println(lineNumber);	
}
public void table() throws IOException{

	boolean exists = true;

	File transaction = new File("Transaction" + LoginGUI.username + ".csv");
	String f = "Transaction" + LoginGUI.username + ".csv";
	if(!transaction.exists()){

	   	  System.out.println("File does not exist, Please add a Transaction");
	   	  exists = false;
	   		   	  }
	if(exists == true){
		BufferedReader out = null;
		try {
			out = new BufferedReader(new FileReader(f));
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	String strLine = null;

    int row = 0;
	int col = 0;

	while((strLine = out.readLine()) != null)
	        {
	        StringTokenizer st = new StringTokenizer(strLine,",");
	        while (st.hasMoreTokens())
	        {
	            //get next token and store it in the array
	            data[row][col] = st.nextToken();
	            col++;


	        }

	        col = 0;
	        row++;
	        }

	}

}
public void WeeklyCashFlow(){
	WspSpentCashFlow = 0;
	WspIncomeCashFlow = 0;
	WspBudgetCashFlow = getbudget();
	// Get calendar set to current date and time
	Calendar c = GregorianCalendar.getInstance();
	c.setFirstDayOfWeek(Calendar.MONDAY);
	// Set the calendar to monday of the current week
	int weekstart1 = Calendar.DAY_OF_WEEK;
	int weekstart2 = Calendar.MONDAY;
	c.set(weekstart1,weekstart2);
	System.out.println(weekstart1 + " " + weekstart2);
	// Print dates of the current week starting on Monday
	DateFormat df = new SimpleDateFormat("dd MMM yyyy");
	String Weekdate = df.format(c.getTime());
System.out.println("Day of the Week: " +c.get(Calendar.DAY_OF_WEEK) );
    System.out.println("Array list: " + lineNumber);
	for(int v = 0; v < lineNumber; v++){
	Weekdate = df.format(c.getTime());
	//System.out.println("V value: " + v);
    	//System.out.println("Date is " + data[v][0]);

    	//System.out.println(weekstart1 + " " + weekstart2);
    	c.set(weekstart1, weekstart2);

    	for (int i = 0; i < 7; i++) {

    	System.out.println("I value: " + i);
    	Weekdate = df.format(c.getTime());
    	c.add(Calendar.DATE, 1);
    	//System.out.println(Weekdate);
    	if(Weekdate.equals(data[v][0])){
    		//System.out.println("Date that matches is " + data[v][0]);
    		if(data[v][3].equals("Withdraw")){
    			System.out.println("Withdraw Before: " + WspSpentCashFlow);
    			WspSpentCashFlow = Double.parseDouble(data[v][2]) + WspSpentCashFlow;
    			System.out.println("Withdraw After: " + WspSpentCashFlow);
    			
    		}
                if(data[v][3].equals("Deposit")){
                    WspIncomeCashFlow = WspIncomeCashFlow + Double.parseDouble(data[v][2]);
                    System.out.println("Income: " + WspIncomeCashFlow);
                    
                }

    		    	}

    	}
    	c.add(Calendar.DATE, -7);
    }
	WspBudgetCashFlow = (((getbudget())/7) + (WspIncomeCashFlow - WspSpentCashFlow));
	System.out.println(WspIncomeCashFlow);
	System.out.println(WspSpentCashFlow);
	System.out.println(WspBudgetCashFlow);
        
}
//public void MonthlyCashFlow(){
	/*MspSpentCashFlow = 0;
	MspIncomeCashFlow = 0;
	MspBudgetCashFlow = getbudget();
	// Get calendar set to current date and time
	Calendar c = GregorianCalendar.getInstance();

	// Set the calendar to monday of the current week
	int monthstart1 = Calendar.DAY_OF_MONTH;
	int monthstart2 = Calendar.MONDAY;
	c.set(monthstart1,monthstart2);
	System.out.println(monthstart + " " + weekstart2);
	// Print dates of the current week starting on Monday
	DateFormat df = new SimpleDateFormat("dd MMM yyyy");
	String Weekdate = df.format(c.getTime());
System.out.println("Day of the Week: " +c.get(Calendar.DAY_OF_WEEK) );
    System.out.println("Array list: " + lineNumber);
	for(int v = 0; v < lineNumber; v++){
	Weekdate = df.format(c.getTime());
	//System.out.println("V value: " + v);
    	//System.out.println("Date is " + data[v][0]);

    	//System.out.println(weekstart1 + " " + weekstart2);
    	c.set(weekstart1, weekstart2);

    	for (int i = 0; i < 7; i++) {

    	System.out.println("I value: " + i);
    	Weekdate = df.format(c.getTime());
    	c.add(Calendar.DATE, 1);
    	//System.out.println(Weekdate);
    	if(Weekdate.equals(data[v][0])){
    		//System.out.println("Date that matches is " + data[v][0]);
    		if(data[v][3].equals("Withdraw")){
    			System.out.println("Withdraw Before: " + WspSpentCashFlow);
    			WspSpentCashFlow = Double.parseDouble(data[v][2]) + WspSpentCashFlow;
    			System.out.println("Withdraw After: " + WspSpentCashFlow);
    			
    		}
                if(data[v][3].equals("Deposit")){
                    WspIncomeCashFlow = WspIncomeCashFlow + Double.parseDouble(data[v][2]);
                    System.out.println("Income: " + WspIncomeCashFlow);
                    
                }

    		    	}

    	}
    	c.add(Calendar.DATE, -7);
    }
	WspBudgetCashFlow = (((getbudget())/7) + (WspIncomeCashFlow - WspSpentCashFlow));
	System.out.println(WspIncomeCashFlow);
	System.out.println(WspSpentCashFlow);
	System.out.println(WspBudgetCashFlow);
        
}
}*/
public double WeeklyForecast(){
	Calendar c = GregorianCalendar.getInstance();
	int dayofweek = c.get(Calendar.DAY_OF_WEEK);
	WspForecast = WspBudgetCashFlow * (7-dayofweek);
    return WspForecast;
}
public void MonthlyForecast(){

}
public void YearlyForecast(){

}
public void createMainGUI() throws IOException {
	JPanel bottomside = new JPanel(new GridBagLayout());
	JPanel topside = new JPanel(new GridBagLayout());
	double screenheight = screenSize.height * 0.95;
	double screenwidth = screenSize.width * 0.98;
	int tablewidth = (int) (screenSize.width * 0.85);

	//Northwest Panel
	GridBagConstraints n = new GridBagConstraints();

	n.insets = new Insets(10,10,10,10);
	NameAccount.setText("Main Account");
	NameAccount.setOpaque(true);
	n.fill = GridBagConstraints.HORIZONTAL;
	
	
	n.gridx = 0;
    n.gridy = 0;
    n.anchor = GridBagConstraints.FIRST_LINE_START	;
   	topside.add(NameAccount,n);
   	n.gridx = 0;
   	n.gridy = 1;
   	n.fill = GridBagConstraints.HORIZONTAL;
    topside.add(test,n);
    topside.setBackground(Color.DARK_GRAY);
   	n.fill = GridBagConstraints.VERTICAL;

	//Southwest Panel

   	GridBagConstraints sw = new GridBagConstraints();
   	sw.insets = new Insets(10,10,10,0);
   	sw.anchor = GridBagConstraints.FIRST_LINE_START;
	sw.gridx = 0;
	sw.gridy = 0;
	BLbl.setForeground(Color.white);
	bottomside.add(BLbl,sw);
	sw.gridy = 1;
   	XLbl.setForeground(Color.white);

	bottomside.add(XLbl,sw);

	bottomside.setBackground(Color.DARK_GRAY);
	jpSW.add(topside,BorderLayout.NORTH);
	jpSW.setBackground(Color.DARK_GRAY);
	jpSW.add(bottomside,BorderLayout.SOUTH);
	//Menu
	menubar.add(File);
    File.add(NewTransaction);
	File.add(Exit);

	//Table

	table();
	JTable Transaction = new JTable(data, columnNames);
	newbalance();

	BLbl.setText("Balance: " + "£ " + Integer.toString((int) balance));
	XLbl.setText("Budget: " + "£ " + newbudget());

	JScrollPane scrollPane = new JScrollPane(Transaction);
	scrollPane.setPreferredSize(new Dimension(tablewidth,810));
	scrollPane.setBackground(Color.white);
	Transaction.setBackground(Color.white);

	Transaction.setBorder(BorderFactory.createLineBorder(Color.BLACK,1));
	Transaction.setEditingRow(0);

	//Panel  settings

	Mainpane.addTab("Transactions", jp1);
	Mainpane.addTab("Cash Flow", jp3);
	Mainpane.addTab("Forecast", jp2);
	//Forecast Pane
	JPanel fpN = new JPanel(new BorderLayout(20,10));
	JPanel fpNW = new JPanel(new GridBagLayout());
	JPanel fpNN = new JPanel(new GridBagLayout());
	JPanel fpNE = new JPanel(new GridBagLayout());

	GridBagConstraints NW = new GridBagConstraints();
	NW.insets = new Insets(10,10,10,10);
	NW.gridx = 0;
	NW.gridy = 0;
    fpNW.setBorder(BorderFactory.createLineBorder(Color.black));
	fpNW.add(WeekForecast,NW);
    NW.anchor = GridBagConstraints.FIRST_LINE_START;
    NW.gridy = 1;
    fpNW.add(WeekIncome,NW);
    NW.gridy = 2;
    fpNW.add(WeekSpent,NW);
    NW.gridy = 3;
	fpNW.add(WeekBudget,NW);	
	WeeklyCashFlow();
	CWeekSpentForecast.setText(Double.toString(WspForecast));
    NW.gridx = 1;
	NW.gridy = 1;
	fpNW.add(CWeekIncomeForecast,NW);
	NW.gridy = 2;
	fpNW.add(CWeekSpentForecast,NW);
	NW.gridy = 3;
	fpNW.add(CWeekBudgetForecast,NW);

	GridBagConstraints NN = new GridBagConstraints();
	NN.insets = new Insets(10,100,10,100);
	NN.gridx = 0;
	NN.gridy = 0;
	fpNN.setBorder(BorderFactory.createLineBorder(Color.black));
	fpNN.add(MonthForecast,NN);
	NN.anchor = GridBagConstraints.FIRST_LINE_START;
	NN.gridy = 1;
    fpNN.add(MonthIncome,NN);
    NN.gridy = 2;
    fpNN.add(MonthSpent,NN);
    NN.gridy = 3;
    fpNN.add(MonthBudget,NN);

   

	GridBagConstraints NE = new GridBagConstraints();
	NE.insets = new Insets(10,10,10,10);
	NE.gridx = 0;
	NE.gridy = 0;
	fpNE.setBorder(BorderFactory.createLineBorder(Color.black));
	fpNE.add(YearForecast,NE);
    NE.anchor = GridBagConstraints.FIRST_LINE_START;
	NE.gridy = 1;
    fpNE.add(YearIncome,NE);
    NE.gridy = 2;
    fpNE.add(YearSpent,NE);
    NE.gridy = 3;
    fpNE.add(YearBudget,NE);

	fpN.add(fpNW,BorderLayout.WEST);        
	fpN.add(fpNN,BorderLayout.CENTER);        
	fpN.add(fpNE,BorderLayout.EAST);
	jp2.add(fpN,BorderLayout.NORTH);
	
	//Cash flow
	JPanel EpN = new JPanel(new BorderLayout(10,10));
	JPanel EpNW = new JPanel(new GridBagLayout());
	JPanel EpNN = new JPanel(new GridBagLayout());
	JPanel EpNE = new JPanel(new GridBagLayout());
	JPanel EpS = new JPanel(new GridBagLayout());
	
	//Cash Flow North Panel West
	GridBagConstraints ENW = new GridBagConstraints();
	ENW.insets = new Insets(10,10,10,10);
	ENW.gridx = 0;
	ENW.gridy = 0;
	EpNW.add(WeeklyCashflow,ENW);
	ENW.gridy = 1;
	EpNW.add(WeekIncome,ENW);
	ENW.gridy = 2;
	EpNW.add(WeekSpent,ENW);
	ENW.gridy = 3;
	EpNW.add(WeekBudget,ENW);
	ENW.gridx = 1;
	ENW.gridy = 1;
	WeeklyIncomeCashflow.setText(Double.toString(WspIncomeCashFlow));	
	EpNW.add(WeeklyIncomeCashflow,ENW);
	ENW.gridy = 2;
	WeeklySpentCashflow.setText(Double.toString(WspSpentCashFlow));	
	EpNW.add(WeeklySpentCashflow,ENW);
	ENW.gridy = 3;
	WeeklyBudgetCashflow.setText(Double.toString(WspBudgetCashFlow));	
	EpNW.add(WeeklyBudgetCashflow,ENW);
	EpNW.setBorder(BorderFactory.createLineBorder(Color.black));	
	EpN.add(EpNW,BorderLayout.WEST);	
	
	//Cash Flow North Panel Center	
	GridBagConstraints ENN = new GridBagConstraints();	
	ENN.insets = new Insets(10,10,10,10);
	ENN.gridx = 0;
	ENN.gridy = 0;
	EpNN.add(MonthlyCashflow,ENN);
	ENN.gridy = 1;
	EpNN.add(MonthIncome,ENN);
	ENN.gridy = 2;
	EpNN.add(MonthSpent,ENN);
	ENN.gridy = 3;
	EpNN.add(MonthBudget,ENN);	
	EpNN.setBorder(BorderFactory.createLineBorder(Color.black));	
	EpN.add(EpNN,BorderLayout.CENTER);
	
	//Cash Flow North Panel East	
	GridBagConstraints ENE = new GridBagConstraints();
	ENE.insets = new Insets(10,10,10,10);
	ENE.gridx = 0;
	ENE.gridy = 0;
	EpNE.add(YearlyCashflow,ENE);
	ENE.gridy = 1;
	EpNE.add(YearIncome,ENE);
	ENE.gridy = 2;
	EpNE.add(YearSpent,ENE);
	ENE.gridy = 3;
	EpNE.add(YearBudget,ENE);	
	EpNE.setBorder(BorderFactory.createLineBorder(Color.black));	
	EpN.add(EpNE,BorderLayout.EAST);
	
	jp3.add(EpN,BorderLayout.NORTH); //Add North Panel to pane
	
	//South Panel 
	GridBagConstraints SP = new GridBagConstraints();
	SP.gridx = 0;
	SP.gridy = 0;
	EpS.add(CashFlowTextField,SP);
	SP.gridx = 1;
	EpS.add(CashFlowSearchButton,SP);
	SP.gridx = 0;
	SP.gridx = 0;
	
	//TabPane
	GridBagConstraints tb = new GridBagConstraints();
	tb.anchor = GridBagConstraints.CENTER;
	jp1.add(scrollPane,tb);

	//MainFrame
	mainframe.setJMenuBar(menubar);

	//settings
	mainframe.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
	mainframe.getContentPane().setBackground(Color.DARK_GRAY);
	mainframe.getContentPane().add(Mainpane, BorderLayout.EAST);
	mainframe.pack();
	mainframe.add(jpSW,BorderLayout.WEST);
	mainframe.setVisible(true);
	mainframe.setSize((int) screenwidth, (int) screenheight );
}

}
