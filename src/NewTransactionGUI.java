import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.DateFormat;
import java.text.DateFormatSymbols;
import java.text.NumberFormat;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFormattedTextField;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JSpinner;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SpinnerDateModel;
import javax.swing.SpinnerListModel;
import javax.swing.SpinnerModel;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;



public class NewTransactionGUI {
	String TypeAry[] = {"Withdraw", "Deposit"};
	double balance = 0;


	Calendar calendar = new GregorianCalendar(2008, Calendar.JUNE, 8);
	Date now = new Date();
	final SpinnerDateModel model = new SpinnerDateModel(now, null, now,
            Calendar.DAY_OF_WEEK);
    JSpinner spinner = new JSpinner(model);
    final DateFormat df = new SimpleDateFormat("dd MMM yyyy");
    JSpinner.DateEditor editor = new JSpinner.DateEditor(spinner,"dd MMM yyyy");


	JLabel Pye = new JLabel("Payee: ");
	JLabel Dte = new JLabel("Date: ");
	JLabel Amount = new JLabel("Amount:");
	JLabel Type = new JLabel("Type: ");
	JLabel Notes = new JLabel("Notes: ");

	JTextField PyeTxt = new JTextField(12);
	JTextField AmtTxt = new JTextField(12);

	JComboBox TypeTxt = new JComboBox(TypeAry);

	JTextArea NoteFld = new JTextArea(10, 25);

	JButton okbtn = new JButton("OK");
	JButton cnclbtn = new JButton("Cancel");

	JFrame JFAT = new JFrame("Add a New Transaction");
	JPanel JPAT = new JPanel(new GridBagLayout());
	public void NTGM() {

		createNewTransactionGUI();
		ACL();
	}
	public double countbalance(){
		double newAmount = Double.parseDouble(AmtTxt.getText());
		double currentAmount = Double.parseDouble(MainGUI.Amount.getText());
		if(TypeTxt.getSelectedItem().equals("Withdraw")){
			balance = currentAmount - newAmount;
		} else if(TypeTxt.getSelectedItem().equals("Deposit")){
			balance = currentAmount + newAmount;
		}
		System.out.println("Balance: " + balance);
		System.out.println("Current Amount: " + currentAmount);
		System.out.println("New Amount: " + newAmount);
		return balance;
	}
	public boolean PayeeEntered(){
		boolean payeeentered = true;
		if (PyeTxt.getText().isEmpty()){
			payeeentered = false;
		}
		return payeeentered;
	}
	public  boolean datecheck() {
        boolean datebefore = true;
        Date value = (Date)model.getValue();
        Date today = new java.util.Date();
        System.out.println("Today's Date: " + today);
        System.out.println("Entered Date: " + value);
        if(today.before(value)){
        	datebefore = false;
        	System.out.println("Today's date is after");
        }

        return datebefore;
    }
	public boolean amountentered(){
		boolean amountentered = true;
		if(AmtTxt.getText().isEmpty() ){
			amountentered = false;
		}
		try {
		    double x = Double.parseDouble(AmtTxt.getText());
		   
		    System.out.println(x);
		}
		catch(NumberFormatException nFE) {
		    System.out.println("Not an Integer");
		    amountentered = false;
		}

		return amountentered;

	}
	public void SFle() {
		String generateCSVFile = "Transaction" + LoginGUI.username + ".csv";
		File f;

	    String sBalance = Double.toString(countbalance());

		f = new File("Transaction" + LoginGUI.username + ".csv");



			try
			{
			    FileWriter writer = new FileWriter(generateCSVFile, true);

			    BufferedWriter out = new BufferedWriter(writer);


			    Date value = (Date)model.getValue();
			    out.append(df.format(value));
			    out.append(',');
			    out.append(PyeTxt.getText());
			    out.append(',');
			    String TypeString = (String)TypeTxt.getSelectedItem();
			    out.append(',');
			    out.append(AmtTxt.getText());
			    out.append(',');
			    out.append(TypeString);
			    out.append(',');
			    System.out.println("Balance " + balance);
			    System.out.println("SBalance " + sBalance);
			    out.append(sBalance);
			    out.append('\n');

			    out.flush();
			    out.close();

			}
			catch(IOException e)
			{
			     e.printStackTrace();
			}
		    }
public boolean failsafe(){
	boolean failsafe = false;
	if(datecheck() == true && amountentered() == true && PayeeEntered() == true){
		failsafe = true;
	}

	return failsafe;

}
public void ACL() {
	okbtn.addActionListener(new ActionListener() {
        public void actionPerformed(ActionEvent event) {
        	if(failsafe() == true){
        	SFle();
        	JFAT.setVisible(false);

        	MainGUI mg = new MainGUI();
                
        	try {
                    
				mg.maincalls();
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
            System.out.println("SAVED");
        }	else {
		System.out.println("Something went wrong");
	}}});
}

public void createNewTransactionGUI(){
	//Grid Layout
	GridBagConstraints c = new GridBagConstraints();

	c.insets = new Insets(10,10,10,10);
	c.anchor = GridBagConstraints.FIRST_LINE_START;
	c.gridx = 0;
	c.gridy = 1;
	JPAT.add(Pye,c);
	c.gridx = 1;
	c.gridy = 1;
	JPAT.add(PyeTxt,c);
	c.gridx = 0;
	c.gridy = 2;
	JPAT.add(Dte,c);
	c.gridx = 1;
	c.gridy = 2;

    spinner.setEditor(editor);
    spinner.addChangeListener(new ChangeListener()
    {
        public void stateChanged(ChangeEvent e)
        {
            Date value = (Date)model.getValue();
            Date next = (Date)model.getNextValue();
            if(value != null && next != null)
                System.out.println("value = " + df.format(value) + "\t" +
                                   "next = " + df.format(next));
        }

		public void stateChanged1(ChangeEvent arg0) {
			// TODO Auto-generated method stub

		}
    });
	JPAT.add(spinner,c);
	c.gridx = 0;
	c.gridy = 3;
	JPAT.add(Amount,c);
	c.gridx = 1;
	c.gridy = 3;
	JPAT.add(AmtTxt,c);
	c.gridx = 0;
	c.gridy = 4;
	JPAT.add(Type,c);
	c.gridx = 1;
	c.gridy = 4;
	JPAT.add(TypeTxt,c);
	c.gridx = 0;
	c.gridy = 5;
	JPAT.add(Notes,c);
	c.gridx = 0;
	c.gridy = 6;
	NoteFld.setBorder(BorderFactory.createLineBorder(Color.black));
	c.gridwidth = 3;
	JPAT.add(NoteFld,c);
	c.gridx = 0;
	c.gridy = 7;
	JPAT.add(okbtn,c);
	c.gridx = 1;
	c.gridy = 7;
	JPAT.add(cnclbtn,c);

	JFAT.pack();
  	JFAT.setLocationRelativeTo(null);
	JFAT.add(JPAT, BorderLayout.NORTH);
	JFAT.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
	JFAT.setSize(400,500);
	JFAT.setVisible(true);
}

}
