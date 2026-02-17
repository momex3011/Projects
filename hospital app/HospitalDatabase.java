import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class HospitalDatabase {
    private String url;
    private String username;
    private String password;

    public HospitalDatabase(String url, String username, String password) {
        this.url = url;
        this.username = username;
        this.password = password;
    }

    public List<Patient> getAllPatients() throws SQLException {
        List<Patient> patients = new ArrayList<>();
        try (Connection connection = DriverManager.getConnection(url, username, password);
             Statement statement = connection.createStatement();
             ResultSet resultSet = statement.executeQuery("SELECT * FROM patients")) {

            while (resultSet.next()) {
                int patientId = resultSet.getInt("patient_id");
                String name = resultSet.getString("name");
                String address = resultSet.getString("address");
                String phone = resultSet.getString("phone");
                Patient patient = new Patient(name, address, phone);
                patient.setPatientId(patientId);
                patients.add(patient);
            }
        }
        return patients;
    }

    public void addPatient(Patient patient) throws SQLException {
        try (Connection connection = DriverManager.getConnection(url, username, password);
             PreparedStatement statement = connection.prepareStatement("INSERT INTO patients (name, address, phone) VALUES (?, ?, ?)")) {

            statement.setString(1, patient.getName());
            statement.setString(2, patient.getAddress());
            statement.setString(3, patient.getPhone());
            statement.executeUpdate();
        }
    }

    public Patient getPatientById(int patientId) throws SQLException {
        try (Connection connection = DriverManager.getConnection(url, username, password);
             PreparedStatement statement = connection.prepareStatement("SELECT * FROM patients WHERE patient_id = ?")) {

            statement.setInt(1, patientId);
            try (ResultSet resultSet = statement.executeQuery()) {
                if (resultSet.next()) {
                    String name = resultSet.getString("name");
                    String address = resultSet.getString("address");
                    String phone = resultSet.getString("phone");
                    Patient patient = new Patient(name, address, phone);
                    patient.setPatientId(patientId);
                    return patient;
                }
            }
        }
        return null;
    }

    public void updatePatient(Patient patient) throws SQLException {
        // Implement update logic here if needed
    }
}
