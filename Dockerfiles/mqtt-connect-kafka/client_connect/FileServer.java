import com.sun.net.httpserver.*;

import java.io.*;
import java.net.InetSocketAddress;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public class FileServer {

    public static void main(String[] args) throws IOException {
        int port = 8080;
        String baseDir = "/tmp"; // Specify the directory containing the files to be served

        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/", new MyHandler(baseDir));
        server.setExecutor(null); // creates a default executor
        server.start();

        System.out.println("Server is running on port " + port);
    }

    static class MyHandler implements HttpHandler {
        private final String baseDir;

        public MyHandler(String baseDir) {
            this.baseDir = baseDir;
        }

        @Override
        public void handle(HttpExchange t) throws IOException {
            String requestMethod = t.getRequestMethod();
            if (requestMethod.equalsIgnoreCase("GET")) {
                handleGetRequest(t);
            } else {
                sendResponse(t, 405, "Method Not Allowed");
            }
        }

        private void handleGetRequest(HttpExchange t) throws IOException {
            Headers headers = t.getResponseHeaders();
            headers.add("Content-Type", "application/octet-stream");

            String uri = t.getRequestURI().toString();
            String filePath = baseDir + uri;

            File file = new File(filePath);
            if (file.exists()) {
                if (file.isDirectory()) {
                    sendDirectoryContents(t, file);
                } else {
                    sendFile(t, file);
                }
            } else {
                sendResponse(t, 404, "File Not Found");
            }
        }

        private void sendDirectoryContents(HttpExchange t, File directory) throws IOException {
            File zipFile = createZipFile(directory);
            sendFile(t, zipFile);
            zipFile.delete(); // Delete the temporary zip file after sending
        }

        private File createZipFile(File directory) throws IOException {
            Path sourcePath = Paths.get(directory.getPath());
            String zipFileName = directory.getName() + ".zip";
            Path zipPath = Files.createTempFile(zipFileName, "");

            try (ZipOutputStream zos = new ZipOutputStream(new FileOutputStream(zipPath.toFile()))) {
                Files.walkFileTree(sourcePath, new SimpleFileVisitor<Path>() {
                    @Override
                    public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                        String relativePath = sourcePath.relativize(file).toString();
                        zos.putNextEntry(new ZipEntry(relativePath));
                        Files.copy(file, zos);
                        zos.closeEntry();
                        return FileVisitResult.CONTINUE;
                    }

                    @Override
                    public FileVisitResult visitFileFailed(Path file, IOException exc) throws IOException {
                        return FileVisitResult.CONTINUE;
                    }
                });
            }

            return zipPath.toFile();
        }

        private void sendFile(HttpExchange t, File file) throws IOException {
            byte[] fileBytes = Files.readAllBytes(file.toPath());
            t.sendResponseHeaders(200, fileBytes.length);
            OutputStream os = t.getResponseBody();
            os.write(fileBytes);
            os.close();
        }

        private void sendResponse(HttpExchange t, int statusCode, String message) throws IOException {
            t.sendResponseHeaders(statusCode, message.length());
            OutputStream os = t.getResponseBody();
            os.write(message.getBytes());
            os.close();
        }
    }
}
