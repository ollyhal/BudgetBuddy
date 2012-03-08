import java.awt.BorderLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.StringTokenizer;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JTextField;




public class LoginGUI extends JFrame {
	
//Declarations	

JLabel Username = new JLabel("Username");
JLabel Password = new JLabel("Password");
JLabel UserNot = new JLabel("Username not found");

JLabel PassNot = new JLabel("Password is wrong");

static JTextField UsernameField = new JTextField(10);
JPasswordField PasswordField = new JPasswordField(10);
JButton LoginBtn = new JButton("Login");
JButton RegisterBtn = new JButton("Register");
JButton CancelBtn = new JButton("Cancel");
JFrame Login = new JFrame("Budget Buddy 0.2");
JPanel pane = new JPanel(new GridBagLayout());

Boolean Csvfile = true;
Boolean Loginbln = true;
Boolean Usermatch = false;

public static String username;

public void LoginMain() 	{
		
	//Create GUI
	CreateLoginGUI();
	//Call Actionlisteners
  	LoginAL();
}
public static String getuser(){
	username = UsernameField.getText();
	return username;
}

public void RFile() throws IOException { 
	
	File generateCSVFile = new File("login.csv");
	String f = "login.csv";
	
	 if(!generateCSVFile.exists()){
   	 
   	  System.out.println("File does not exist, Please Register");
   	  Csvfile = false;
   	  }
	 
	if(Csvfile == true){
    try {
		BufferedReader out = new BufferedReader(new FileReader(f));
		String strLine = null;
		StringTokenizer st = null;
		GridBagConstraints c = new GridBagConstraints(); 
	  	
	  	c.insets = new Insets(10,10,10,10);       
		int lineNumber = 0, tokenNumber = 0;
		while( (f = out.readLine()) != null )
		{ 
			
			lineNumber++;
			//break comma separated line using ","
			st = new StringTokenizer(f, ",");
                       
			if (UsernameField.getText().equals(st.nextToken())){
                            System.out.println("Match");
                            Usermatch = true;
                            Loginbln = false;
                            if (PasswordField.getText().equals(st.nextToken())){
                               System.out.println("Password matches too");
                               Loginbln = true;
                               
                            } else if(Loginbln == false){
                            	System.out.println("Password does not match");
                            	PassNot.setVisible(true);
                            	UserNot.setVisible(false);
                            	
                            }  else { 
                            	UserNot.setVisible(true);
                            	PassNot.setVisible(false);
                            }
                            
                        
			}
			 if(Loginbln == false && Usermatch == false) { 
	             	PassNot.setVisible(true);
	             	UserNot.setVisible(false);
				 }
	             else if(Loginbln == true && Usermatch == false) {
	            	 UserNot.setVisible(true);
	             }
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
	}
	if(Loginbln == true && Usermatch == true){
		Login.setVisible(false);
			
		MainGUI ex = new MainGUI();
		ex.rmain ();
	}
}
   

public void CreateLoginGUI(){
	  	 	
   	//Grid Layout
	GridBagConstraints c = new GridBagConstraints(); 
  	
  	c.insets = new Insets(10,10,10,10);
  	
  	c.gridx = 0;
    c.gridy = 1;
    pane.add(Username,c);
    c.gridx = 0;
    c.gridy = 2;
    pane.add(Password,c);
  	c.gridx = 1;
  	c.gridy = 1;
  	pane.add(UsernameField,c);
  	c.gridx = 1;
  	c.gridy = 2	;	
  	pane.add(PasswordField,c);
  	c.gridx = 2;
	c.gridy = 1;
	pane.add(UserNot,c);
	UserNot.setVisible(false);
	c.gridx = 2;
	c.gridy = 2;
	pane.add(PassNot, c);
	PassNot.setVisible(false);
  	c.gridx = 0;
  	c.gridy = 3;
  	pane.add(LoginBtn,c);
  	c.gridx = 1;
  	c.gridy = 3;
  	pane.add(CancelBtn,c);
  	c.gridx = 2;
  	c.gridy = 3;
  	pane.add(RegisterBtn,c);
  	
   	//Add to Frame
  	Login.add(pane,BorderLayout.CENTER);
  	  	 	
	//Properties 
    Login.pack();
  	Login.setLocationRelativeTo(null);
  	Login.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
	Login.setSize(400,200);	
	Login.setVisible(true);
	Login.setResizable(false);
	
}	

private class LoginLst implements ActionListener {
public void actionPerformed(ActionEvent arg0) {
	try {
		RFile();
	} catch (IOException e) {
		// TODO Auto-generated catch block
		e.printStackTrace();
	}
   
 }
}
public void LoginAL()  {
	LoginLst Llst = new LoginLst();
	LoginBtn.addActionListener(Llst);

	

	CancelBtn.addActionListener(new ActionListener() {
        public void actionPerformed(ActionEvent event) {                
        	MainGUI mg = new MainGUI();
        	try {
				mg.rmain();
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
        }
    });
	UsernameField.addKeyListener(new KeyAdapter() {
        public void keyPressed(KeyEvent e) {
            int key = e.getKeyCode();
            if (key == KeyEvent.VK_ENTER) {
            	getuser();
            	try {
					RFile();
				} catch (IOException e1) {
					// TODO Auto-generated catch block
					e1.printStackTrace();
				}      
                            }
            }
          }
       );
	PasswordField.addKeyListener(new KeyAdapter() {
        public void keyPressed(KeyEvent e) {
            int key = e.getKeyCode();
            if (key == KeyEvent.VK_ENTER) {
            	getuser();
            	try {
					RFile();
				} catch (IOException e1) {
					// TODO Auto-generated catch block
					e1.printStackTrace();
				}      
                            }
            }
          }
       );

	LoginBtn.addActionListener(new ActionListener() {
        public void actionPerformed(ActionEvent event) {                
        	getuser();
            try {
				RFile();
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
            
        }
    });
	
	RegisterBtn.addActionListener(new ActionListener() {
        public void actionPerformed(ActionEvent event) {                
            Login.setVisible(false);
            RegisterGUI rg = new RegisterGUI();
            rg.RegisterMain();
            
            
        }
    });
}

}
