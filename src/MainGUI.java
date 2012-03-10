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
import javax.swing.border.EmptyBorder;


public class MainGUI {
	
//Declarations 
	
Object[] columnNames = {"Date","Payee","Amount","Type","Balance"};
 
public static int lineNumber = 0;
int tokenNumber = 0;
String[][] data = new String[lineNumber][5];
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

JPanel jpNW = new JPanel(new GridBagLayout());
JPanel jpSW = new JPanel(new BorderLayout());

Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();
//Forecast Pane
JLabel MonthForecast = new JLabel("Monthly Forecast");
JLabel MonthIncome = new JLabel("Income: ");
JLabel MonthIncomeBalnce = new JLabel();
JLabel MonthSpent = new JLabel("Spent: ");
JLabel MonthBudget = new JLabel("Budget: ");
JLabel WeekForecast = new JLabel("Weekly Forecast");
JLabel WeekIncome = new JLabel("Income: ");
JLabel WeekSpent = new JLabel("Spent: ");
JLabel WeekBudget = new JLabel("Budget: ");
JLabel YearForecast = new JLabel("Yearly Forecast");
JLabel YearIncome = new JLabel("Income: ");
JLabel YearSpent = new JLabel("Spent: ");
JLabel YearBudget = new JLabel("Budget: ");
JLabel CustomForecast = new JLabel("Custom Forecast");

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

public double newbudget(){
	for(int i = 0; i < lineNumber; i++){
		
		if(data[i][3].equals("Withdraw")){
			budget = budget - Double.parseDouble(data[i][2]);
			System.out.println("Withdraw");
		}
	}
	bLeft.setText(Double.toString(budget));
	return budget;
	
}
public double newbalance(){
	
	for(int i = 0; i < lineNumber; i++){
		
		if(data[i][3].equals("Withdraw")){
			balance = balance - Double.parseDouble(data[i][2]);
			System.out.println("Withdraw");
		}else if(data[i][3].equals("Deposit")){
				balance = Double.parseDouble(data[i][2]) + balance;
				System.out.println("Deposit");
		}
	}
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
	n.ipadx = 80;
	n.gridwidth = 3;
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
   	sw.insets = new Insets(10,10,10,10);
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
	JPanel fpN = new JPanel(new BorderLayout());
	JPanel fpNW = new JPanel(new GridBagLayout());
	JPanel fpNN = new JPanel(new GridBagLayout());
	JPanel fpNE = new JPanel(new GridBagLayout());
	
	GridBagConstraints NW = new GridBagConstraints();	
	NW.insets = new Insets(10,100,10,100);
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
	NE.insets = new Insets(10,100,10,100);
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
	//Expenditure
	JPanel EpN = new JPanel(new BorderLayout());
	JPanel EpNW = new JPanel(new GridBagLayout());
	JPanel EpNN = new JPanel(new GridBagLayout());
	JPanel EpNE = new JPanel(new GridBagLayout());
	
	GridBagConstraints ENW = new GridBagConstraints();	
	
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
