import java.awt.Insets;
import java.io.IOException;
import java.text.NumberFormat;

import javax.swing.SwingUtilities;


public class Startup {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		SwingUtilities.invokeLater(new Runnable() {
		
            public void run() {
            	
            	LoginGUI ex = new LoginGUI();
        		ex.LoginMain();
  			  
            }
        });

	}
	}


