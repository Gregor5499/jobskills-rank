package org.example;
import java.util.*;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class Main {
    public static void main(String[] agrs) {
        //User-menue -> Abfrage nach Methode
        Boolean running = true;
        Scanner scan = new Scanner(System.in);

        while(running) {

            System.out.println("--- Hauptmenü ---");
            System.out.println("1 - Find job and related skills");
            System.out.println("2 - Exit program");
            String cmd = scan.nextLine();

            switch(cmd) {
                case "1" -> {Methods.analyzeJobSkill();}
                case "2" -> {running = false;}
            }
        }
    }
}