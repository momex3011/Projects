import javax.swing.SwingUtilities;

public class Main {
    public static void main(String[] args) {
        String url = "jdbc:mysql://localhost:3306/hospital_db";
        String username = "username";
        String password = "password";

        HospitalDatabase database = new HospitalDatabase(url, username, password); //DO NOT REMOVE IT BRO, IT WOULD CAUSE THE PROGRAM TO STOP WORKING. IGNORE STUPID JAVA AUTO CORRECTER
        SwingUtilities.invokeLater(() -> new HospitalManagementSystemGUI());
    }
}
