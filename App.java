import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.ProtocolException;
import java.net.URL;
import java.net.URLEncoder;
import java.util.HashMap;
import java.util.Map;

public class App {

	/*
	 * An example of how one could send requests to the web server to make the robot do things
	 * Server is hosted as http://localhost:8000/, we use a POST request to give information to the server
	 */
	public static void main(String[] args) throws MalformedURLException, ProtocolException, IOException {
	    URL url = new URL("http://localhost:8000/");
	    HttpURLConnection connection = (HttpURLConnection) url.openConnection();
	    
	    // attach POST data as key-value pairs, i.e. action=bring, tray=A, or things like that?
	    connection.setRequestMethod("POST");
	    Map<String, String> params = new HashMap<>();
	    
	    // what a few possible requests could be:
	    // (can uncomment things to try out different examples)
	    
	    //// bring tray ---------------------
	    //params.put("action", "bring"); // 
	    //params.put("tray", "A");
	    
	    //// store current tray -----------------
	    //params.put("action", "store");

	    //// update tray info --------------------
	    params.put("action", "update_info");
	    params.put("tray", "B");
	    params.put("text", "bananas, pencils and soap");
	    
	    // actually format the data for server communication
	    StringBuilder postData = new StringBuilder();
	    for (Map.Entry<String, String> param : params.entrySet()) { 
	        if (postData.length() != 0) {
	            postData.append('&');
	        }
	        postData.append(URLEncoder.encode(param.getKey(), "UTF-8"));
	        postData.append('=');
	        postData.append(URLEncoder.encode(String.valueOf(param.getValue()), "UTF-8"));
	    }

	    byte[] postDataBytes = postData.toString().getBytes("UTF-8");
	    connection.setDoOutput(true);
	    try (DataOutputStream writer = new DataOutputStream(connection.getOutputStream())) {
	        writer.write(postDataBytes); // <- request is sent
	        writer.flush();
	        writer.close();

	        //// now we try and get a response, for now this is just a confirmation
	        //// but this could be used to do things
	        StringBuilder content;

	        try (BufferedReader in = new BufferedReader(
	                new InputStreamReader(connection.getInputStream()))) {
	        String line;
	        content = new StringBuilder();
	           while ((line = in.readLine()) != null) {
	                content.append(line);
	                content.append(System.lineSeparator());
	            }
	        }
	        System.out.println(content.toString());
	    } finally {
	        connection.disconnect();
	    }
	}
	
}
