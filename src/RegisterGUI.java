import java.awt.BorderLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JTextField;
import javax.swing.SwingConstants;




public class RegisterGUI {
//Declarations
	JLabel UsernameLbl = new JLabel("Username");
	JLabel PasswordLbl = new JLabel("Password");
	JLabel CPasswordLbl = new JLabel("Confirm Password");
	JLabel NLbl = new JLabel("");
	JTextField UsernameTxt = new JTextField(10);
	JPasswordField PasswordFld = new JPasswordField(10);
	JPasswordField CPFld = new JPasswordField(10);
	JButton okbtn = new JButton("OK");
	JButton CancelBtn = new JButton("Cancel");
	JFrame RFrame = new JFrame("Budget Buddy 0.2");
	JPanel RPanel = new JPanel(new GridBagLayout());
	JPanel CPanel = new JPanel(new GridBagLayout());
	boolean bun = false;
	boolean bpwd = false;
	
	
	public void CreateRegisterGUI(){ 
	//Grid Layout
	  GridBagConstraints c = new GridBagConstraints(); 
	  GridBagConstraints b = new GridBagConstraints(); 
	  	  	
	  //center panel
	  
	    c.insets = new Insets(10,10,10,10);
	   
	    c.anchor = GridBagConstraints.FIRST_LINE_START;
	    c.fill = GridBagConstraints.HORIZONTAL;
	    c.gridx = 0;
	    c.gridy = 1;
	    RPanel.add(UsernameLbl,c);
	    c.gridx = 0;
	    c.gridy = 2;
	    PasswordLbl.setAlignmentX(SwingConstants.LEFT);
	    RPanel.add(PasswordLbl,c);
	    c.gridx = 0;
	    c.gridy = 3;
	    CPasswordLbl.setAlignmentX(SwingConstants.LEFT);
	    RPanel.add(CPasswordLbl,c);
	  	c.gridx = 1;
	  	c.gridy = 1;  
	  	RPanel.add(UsernameTxt,c);
	  	c.gridx = 1;
	  	c.gridy = 2	;	
	  	RPanel.add(PasswordFld,c);
	  	c.gridx = 1;
	  	c.gridy = 3	;	
	  	RPanel.add(CPFld,c);
	  	c.gridx = 0;
	  	c.gridy = 4;
	  	RPanel.add(okbtn,c);
	  	c.gridx = 3;
	  	c.gridy = 0;
	  	c.gridx = 1;
	  	c.gridy = 4;
	  	c.anchor = GridBagConstraints.FIRST_LINE_END;
	  	RPanel.add(CancelBtn,c);
	  	
	  	//bottom panel 	
	  		  	
	  	CPanel.add(NLbl, b);
	  	
	  	RFrame.add(RPanel,BorderLayout.CENTER);
	  	RFrame.add(CPanel,BorderLayout.AFTER_LAST_LINE);
	  	RFrame.pack();
		RFrame.setLocationRelativeTo(null);
	  	RFrame.setSize(400,230);
	  	RFrame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
	  	RFrame.setVisible(true);
	  	RFrame.setResizable(false);
	  	
	}
	public void RegisterMain() { 
		CreateRegisterGUI();
		RegisterAL();
	  	
	  		
	}
	
	public void SFle() {
		String generateCSVFile = "login.csv";
		File f;
		f = new File("login.csv");
			    if(!f.exists()){
		    	  try {
					f.createNewFile();
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
		    	  System.out.println("New file \"test.csv\" has been created to the current directory");
		    	  }
		
		
			  
			try
			{
			    FileWriter writer = new FileWriter(generateCSVFile, true);
			    BufferedWriter out = new BufferedWriter(writer);
		 
			    out.append(UsernameTxt.getText());
			    out.append(',');
			    out.append(PasswordFld.getText());
			    out.append('\n');
		 		 
			    out.flush();
			    out.close();
			    NLbl.setText("File saved");
                            RFrame.setVisible(false);
                            LoginGUI ex = new LoginGUI();
                            ex.LoginMain();
			}
			catch(IOException e)
			{
			     e.printStackTrace();
			} 
		    }
	
	public void CDL(){
	String username = UsernameTxt.getText();
	String password = PasswordFld.getText();
	String CPFldd = CPFld.getText();
	
	
	if (username.length() == 0){
		NLbl.setText("No username has been entered!");
		bun = true;
	} else if(username.length() < 3 ){
		NLbl.setText("Username is too short");
		bun = true;
	} else if(username.length() > 10){
		NLbl.setText("Username is too long");
		bun = true;
	} else {
		bun = false;
	}
	
	
	if(!password.equals(CPFldd)){
		NLbl.setText("Passwords do not match");
		bpwd = true;
		
		
	} else if(password.length() < 3){
		NLbl.setText("Passwords is too short");
		bpwd = true;
	} else {
		bpwd = false;
	}
	
	
	}
	
	public void RegisterAL(){
		CancelBtn.addActionListener(new ActionListener() {
	        public void actionPerformed(ActionEvent event) {                
	        	RFrame.setVisible(false);
	        	LoginGUI lg = new LoginGUI();
	        	lg.LoginMain();
	                        
	        }
	    });
		okbtn.addActionListener(new ActionListener() {
	        public void actionPerformed(ActionEvent event) {                
	        	CDL();
	        	if(bun == false && bpwd == false){
	        		SFle();
	        		
	        	}
	        	
	        	
	                        
	        }
	    });
		
	}
}
