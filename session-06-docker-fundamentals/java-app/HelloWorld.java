import com.sun.net.httpserver.HttpServer;

import java.io.OutputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

public class HelloWorld {
    public static void main(String[] args) throws Exception {
        int port = 8080;
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/", exchange -> {
            String host = InetAddress.getLocalHost().getHostName();
            String html = "<html><head><title>Java App</title></head>"
                    + "<body style=\"font-family: Arial, sans-serif; text-align: center; margin-top: 120px; background: #fdf6f0;\">"
                    + "<h1 style=\"color: #e76f00;\">Hello World from Java!</h1>"
                    + "<p>Java HttpServer running inside a Docker container</p>"
                    + "<p>Container hostname: <b>" + host + "</b> | Java " + System.getProperty("java.version") + "</p>"
                    + "</body></html>";
            byte[] body = html.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().add("Content-Type", "text/html; charset=utf-8");
            exchange.sendResponseHeaders(200, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        });
        server.start();
        System.out.println("Java app listening on port " + port);
    }
}
