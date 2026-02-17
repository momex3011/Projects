import java.util.ArrayList;
import java.util.List;

public class Patient {
    private int patientId;
    private String name;
    private String address;
    private String phone;
    private List<String> treatments;

    public Patient(String name, String address, String phone) {
        this.name = name;
        this.address = address;
        this.phone = phone;
        this.treatments = new ArrayList<>();
    }

    public int getPatientId() {
        return patientId;
    }

    public void setPatientId(int patientId) {
        this.patientId = patientId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public List<String> getTreatments() {
        return treatments;
    }

    public void addTreatment(String treatment) {
        treatments.add(treatment);
    }

    @Override
    public String toString() {
        return name + "," + address + "," + phone + "," + patientId;
    }

    
}
