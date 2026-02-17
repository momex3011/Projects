import java.io.*;
import java.util.ArrayList;
import java.util.List;

public class HospitalDataHandler {

    public static void savePatientsToFile(List<Patient> patients) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter("patient_data.txt", true))) {
            for (Patient patient : patients) {
                writer.write(patient.toString());
                writer.newLine();
            }
        } catch (IOException e) {
            e.printStackTrace();
            System.err.println("Error saving patients to file: " + e.getMessage());
        }
    }

    public static List<Patient> loadPatientsFromFile() {
        List<Patient> patients = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader("patient_data.txt"))) {
            String line;
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",");
                if (parts.length == 4) {
                    String name = parts[0].trim();
                    String address = parts[1].trim();
                    String phone = parts[2].trim();
                    int patientId = Integer.parseInt(parts[3].trim());
                    Patient patient = new Patient(name, address, phone);
                    patient.setPatientId(patientId);
                    patients.add(patient);
                }
            }
        } catch (IOException | NumberFormatException e) {
            e.printStackTrace();
            System.err.println("Error loading patients from file: " + e.getMessage());
        }
        return patients;
    }
}