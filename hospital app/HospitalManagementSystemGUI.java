import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.ArrayList;
import java.util.List;

public class HospitalManagementSystemGUI extends JFrame {
    private List<Patient> patients;

    public HospitalManagementSystemGUI() {
        setTitle("Hospital Management System");
        setSize(800, 600);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

        JPanel mainPanel = new JPanel(new BorderLayout());

        // Components for patient management
        JPanel patientPanel = new JPanel(new BorderLayout());
        patientPanel.setBorder(BorderFactory.createTitledBorder("Patient Management"));

        JTextArea patientInfoArea = new JTextArea(20, 60);
        patientInfoArea.setEditable(false);
        JScrollPane patientScrollPane = new JScrollPane(patientInfoArea);
        patientPanel.add(patientScrollPane, BorderLayout.CENTER);

        JButton showPatientsButton = new JButton("Show Patients");
        showPatientsButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                displayPatients(patientInfoArea);
            }
        });

        JButton addPatientButton = new JButton("Add Patient");
        addPatientButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                addPatient();
            }
        });

        JButton addTreatmentButton = new JButton("Add Treatment");
        addTreatmentButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                addTreatment(patientInfoArea);
            }
        });

        JPanel buttonPanel = new JPanel();
        buttonPanel.add(showPatientsButton);
        buttonPanel.add(addPatientButton);
        buttonPanel.add(addTreatmentButton);
        patientPanel.add(buttonPanel, BorderLayout.SOUTH);

        // Add patient panel to main panel
        mainPanel.add(patientPanel, BorderLayout.CENTER);

        add(mainPanel);
        setVisible(true);

        // Load existing patient data
        patients = HospitalDataHandler.loadPatientsFromFile();
        if (patients == null) {
            patients = new ArrayList<>();
        }
    }

    private void addPatient() {
        String name = JOptionPane.showInputDialog(null, "Enter Patient Name:");
        if (name == null || name.trim().isEmpty() || !name.matches("[a-zA-Z]+")) {
            JOptionPane.showMessageDialog(null, "Invalid name. Please enter a valid name (letters only).");
            return;
        }
        
        String address = JOptionPane.showInputDialog(null, "Enter Address:");
        int phone;
        try {
            phone = Integer.parseInt(JOptionPane.showInputDialog(null, "Enter Phone Number:"));
        } catch (NumberFormatException e) {
            JOptionPane.showMessageDialog(null, "Invalid phone number format. Please enter a valid integer phone number.");
            return;
        }
        
        int id;
        try {
            id = Integer.parseInt(JOptionPane.showInputDialog(null, "Enter Patient ID:"));
        } catch (NumberFormatException e) {
            JOptionPane.showMessageDialog(null, "Invalid ID format. Please enter a valid integer ID.");
            return;
        }
        
        if (address == null || address.trim().isEmpty()) {
            JOptionPane.showMessageDialog(null, "Address cannot be empty. Please enter a valid address.");
            return;
        }
    
        if (name != null && !name.isEmpty()) {
            Patient patient = new Patient(name, address, String.valueOf(phone));
            patient.setPatientId(id);
            patients.add(patient);
            HospitalDataHandler.savePatientsToFile(patients);
            JOptionPane.showMessageDialog(null, "Patient added successfully!");
        }
    }

    private void displayPatients(JTextArea patientInfoArea) {
        StringBuilder info = new StringBuilder("List of Patients:\n");
        for (Patient patient : patients) {
            info.append("Patient ID: ").append(patient.getPatientId());
            info.append(", Name: ").append(patient.getName());
            info.append(", Address: ").append(patient.getAddress()).append(", Phone: ").append(patient.getPhone()).append("\n");
            info.append("Treatments: ");
            List<String> treatments = patient.getTreatments();
            if (!treatments.isEmpty()) {
                for (String treatment : treatments) {
                    info.append(treatment).append(", ");
                }
                info.setLength(info.length() - 2); // remove the trailing comma and space
            }
            info.append("\n\n");
        }
        patientInfoArea.setText(info.toString());
    }

    private void addTreatment(JTextArea patientInfoArea) {
        JComboBox<String> patientComboBox = new JComboBox<>();
        for (Patient patient : patients) {
            patientComboBox.addItem(patient.getName());
        }

        JPanel inputPanel = new JPanel();
        inputPanel.setLayout(new GridLayout(0, 2));
        inputPanel.add(new JLabel("Select Patient:"));
        inputPanel.add(patientComboBox);

        int result = JOptionPane.showConfirmDialog(null, inputPanel, "Add Treatment", JOptionPane.OK_CANCEL_OPTION);
        if (result == JOptionPane.OK_OPTION) {
            int selectedPatientIndex = patientComboBox.getSelectedIndex();
            if (selectedPatientIndex != -1) {
                String treatment = JOptionPane.showInputDialog(null, "Enter Treatment:");
                if (treatment != null && !treatment.isEmpty()) {
                    Patient patient = patients.get(selectedPatientIndex);
                    patient.addTreatment(treatment);
                    HospitalDataHandler.savePatientsToFile(patients);
                    JOptionPane.showMessageDialog(null, "Treatment added successfully!");
                    displayPatients(patientInfoArea);
                }
            } else {
                JOptionPane.showMessageDialog(null, "Please select a patient.");
            }
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(HospitalManagementSystemGUI::new);
    }
}
