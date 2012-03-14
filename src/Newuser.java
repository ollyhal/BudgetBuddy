
import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JSpinner;
import javax.swing.JTextArea;
import javax.swing.JTextField;


public class Newuser {
Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();	

int frameheight = screenSize.height / 2;
int framewidth = screenSize.width / 2;	

JLabel NameAccount = new JLabel("Namse of Account");
JLabel StartingBalance = new JLabel("Starting Balance" + " (£)");
JLabel setBudget = new JLabel("Set a Monthly Budget" + " (£)");
JLabel Nlbl = new JLabel("testing");

JTextField AccountFld = new JTextField(10);
JTextField StartingFld = new JTextField(10);
public static JTextField BalanceFld = new JTextField(10);

JButton okbtn = new JButton("OK");
JButton cnclbtn = new JButton("Cancel");
JPanel BpNewuser = new JPanel(new GridBagLayout());
JPanel PNewuser = new JPanel(new GridBagLayout());	
JFrame FNewuser = new JFrame("Budget Buddy 0.2");
public static Boolean Newsuccess = false;
public static String Balancestart;
public void nusermain(){ 
	createNewUserGUI();
	ACL();
}

public void createNewUserGUI(){
	
	GridBagConstraints c = new GridBagConstraints(); 
	c.insets = new Insets(10,10,10,10);
	c.gridx = 0;
	c.gridy = 0;	
	PNewuser.add(NameAccount,c);
	c.gridx = 0;
	c.gridy = 1;	
	PNewuser.add(StartingBalance,c);
	c.gridx = 0;
	c.gridy = 2;
	PNewuser.add(setBudget,c);
	c.gridx = 1;
	c.gridy = 0;		
	PNewuser.add(AccountFld,c);
	c.gridx = 1;
	c.gridy = 1;	
	PNewuser.add(StartingFld,c);
	c.gridx = 1;
	c.gridy = 2;
	PNewuser.add(BalanceFld,c);
	c.gridx = 0;
	c.gridy = 3;
	PNewuser.add(okbtn,c);
	c.gridx = 1;
	c.gridy = 3;
	PNewuser.add(cnclbtn,c);
		
	GridBagConstraints b = new GridBagConstraints(); 
	b.insets = new Insets(0,0,0,0);	
	b.gridx = 0;
	b.gridy = 0;
	BpNewuser.add(Nlbl,b);
	
	FNewuser.add(PNewuser,BorderLayout.CENTER);
	FNewuser.add(BpNewuser,BorderLayout.AFTER_LAST_LINE);
	
	FNewuser.pack();
	FNewuser.setSize(350,250);
	FNewuser.setLocationRelativeTo(null);
   	FNewuser.setResizable(false);
	FNewuser.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
	FNewuser.setVisible(true);
	
}

public void savefile(){ 
	
	Calendar currentDate = Calendar.getInstance();
	final DateFormat df = new SimpleDateFormat("dd MMM yyyy"); 
	String dateNow = df.format(currentDate.getTime());
	 
	 try
		{
		    FileWriter writer = new FileWriter(MainGUI.f, true);
		    BufferedWriter out = new BufferedWriter(writer);
		     
		   		    
		    out.append(dateNow);
		    out.append(',');	 
		    out.append("Starting Balance");
		    out.append(',');
		    out.append(StartingFld.getText());
		    out.append(',');
		    out.append("Deposit");	
		    out.append(',');
		    out.append(StartingFld.getText());
		    out.append('\n');
	 		 
		    out.flush();
		    out.close();
		    
		    FNewuser.setVisible(false);
             
		}
		catch(IOException e)
		{
		     e.printStackTrace();
		} 
	 try 
	 {
		 FileWriter writer = new FileWriter(MainGUI.SettingsFile,true);
		 BufferedWriter out = new BufferedWriter(writer);
		 
		 out.append("Setting a Budget");
		 out.append(',');	
		 out.append(BalanceFld.getText());
		 out.flush();
		 out.close();
	 }
	 catch(IOException e)
		{
	     e.printStackTrace();
	} 
	    }
	 

public void ACL() { 
	
	okbtn.addActionListener(new ActionListener() {
        public void actionPerformed(ActionEvent event) { 
        	savefile();
        	Balancestart = AccountFld.getText();
        	FNewuser.setVisible(false);
        	MainGUI mg = new MainGUI();
        	try {
				mg.maincalls();
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
        	Newsuccess = true;
        	
        	
                        
        }
    });
	cnclbtn.addActionListener(new ActionListener() {
        public void actionPerformed(ActionEvent event) {          
        	System.exit(0);
        	
                        
        }
    });
	
}
}
