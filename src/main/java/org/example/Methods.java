package org.example;
import java.net.URI;
import java.util.*;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import com.google.gson.Gson;
import com.google.genai.Client;
import com.google.genai.types.GenerateContentResponse;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

public class Methods {

    public static void analyzeJobSkill(){

        //Abfrage nach Daten und in Variablen speichern
        Scanner scan = new Scanner(System.in);
        System.out.println("Enter job name: ");
        String jobName = scan.nextLine();
        System.out.println("Enter location: ");
        String location = scan.nextLine();

        //Fuer URL encode -> Leerzeichen transformieren
        String URLJobName = URLEncoder.encode(jobName, StandardCharsets.UTF_8);
        String URLLocation = URLEncoder.encode(location, StandardCharsets.UTF_8);

        System.out.println("Searching for job: " + jobName + " in " + location + "!");

        //Zugangsdaten fuer Adzuna aus Umgebungsvariablen lesen (nicht im Code hinterlegen)
        String appId = System.getenv("ADZUNA_APP_ID");
        String appKey = System.getenv("ADZUNA_APP_KEY");
        if (appId == null || appKey == null || appId.isBlank() || appKey.isBlank()) {
            System.out.println("Keine Adzuna-Zugangsdaten gefunden. Bitte ADZUNA_APP_ID und ADZUNA_APP_KEY setzen.");
            return;
        }

        //Client Objekt initialisieren
        HttpClient client1 = HttpClient.newHttpClient();

        StringBuilder allDescriptions = new StringBuilder(); //Großer String

        //Paging -> 5 mal die Request an Afzuna schicken -> eine Seite weiter
        for(int i=1; i<=5; i++) {

            //HTTPS URl fuer Adzuna API mit Daten
            String url = "https://api.adzuna.com/v1/api/jobs/de/search/" + i + "?app_id=" + appId + "&app_key=" + appKey + "&results_per_page=100&what=" + URLJobName + "&where=" + URLLocation + "&max_days_old=365";

            //Request verpacken
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .GET()
                    .build();

            try {
                //Response definieren
                HttpResponse<String> response = client1.send(request, HttpResponse.BodyHandlers.ofString());

                String JSONtext = response.body();
                Gson gson = new Gson();
                AdzunaPojo adzunaData = gson.fromJson(JSONtext, AdzunaPojo.class); //Nach Template der Klasse

                if (adzunaData == null || adzunaData.results == null || adzunaData.results.isEmpty()) { //Leere Inhalte abfaneg
                    break;
                }

                System.out.println("Gefundene Jobs: " + adzunaData.results.size());

                for (Job job : adzunaData.results) {
                    allDescriptions.append(job.description).append("\n"); //An großen String anhaengen -> Einzeln Jobdescription für Jobdescription
                }

            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        try {
            Client client = new Client();

            GenerateContentResponse response1 =
                    client.models.generateContent(
                            "gemini-3.5-flash",
                            "Du bist ein Datenanalyst. Extrahiere aus den folgenden Stellenbeschreibungen " +
                                    "die häufigst genanntesten Fähigkeiten (bevorzugt Anwendungsorientier (Bsp. Python statt Software Engineering)). " +
                                    "Gib mir nur ein Ranking der 10 häufisgten Skills zurück. (Einfache 1.-10. Liste)\n\n" +
                                    "Stellenbeschreibungen:\n" + allDescriptions,
                            null); //Prompt der KI

            System.out.println(response1.text());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}