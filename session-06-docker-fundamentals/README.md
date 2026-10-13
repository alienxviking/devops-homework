# Session 06 - Docker Fundamentals

## Task: Hello World applications with Docker

```
session-06-docker-fundamentals/
├── nodejs-app/    Express server           -> port 3000
├── python-app/    Flask app                -> port 5000
├── java-app/      Java HttpServer (multi-stage JDK -> JRE) -> port 8080
├── Apache-app/    httpd static page        -> port 8081
├── React-app/     React + Vite, built and served by nginx (multi-stage) -> port 8082
└── nginx-app/     nginx static page        -> port 8083
```

Steps followed for every app:

```bash
cd <app-folder>
docker build -t <app>:1.0 .
docker run -d --name <app> -p <host-port>:<container-port> <app>:1.0
docker ps
curl localhost:<host-port>      # and open it in the browser
```

---

## 1. Node.js app

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install --omit=dev
COPY server.js .
EXPOSE 3000
CMD ["npm", "start"]
```

| Build | Run |
|---|---|
| ![](screenshots/01-nodejs-app-build.png) | ![](screenshots/01-nodejs-app-run.png) |

![node browser](screenshots/08-browser-nodejs.png)

## 2. Python app

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

| Build | Run |
|---|---|
| ![](screenshots/02-python-app-build.png) | ![](screenshots/02-python-app-run.png) |

![python browser](screenshots/09-browser-python.png)

## 3. Java app

Two stages: compile with the JDK, then copy only the `.class` file into a smaller JRE image.

```dockerfile
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /src
COPY HelloWorld.java .
RUN javac HelloWorld.java

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /src/*.class .
EXPOSE 8080
CMD ["java", "HelloWorld"]
```

| Build | Run |
|---|---|
| ![](screenshots/03-java-app-build.png) | ![](screenshots/03-java-app-run.png) |

![java browser](screenshots/10-browser-java.png)

## 4. Apache app

```dockerfile
FROM httpd:2.4-alpine
COPY index.html /usr/local/apache2/htdocs/index.html
EXPOSE 80
```

| Build | Run |
|---|---|
| ![](screenshots/04-apache-app-build.png) | ![](screenshots/04-apache-app-run.png) |

![apache browser](screenshots/11-browser-apache.png)

## 5. React app

Stage 1 runs `npm install` + `npm run build` (Vite), stage 2 copies only the `dist/` folder into nginx. The final image has no node_modules.

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

| Build | Run |
|---|---|
| ![](screenshots/05-react-app-build.png) | ![](screenshots/05-react-app-run.png) |

`curl` only returns the empty `<div id="root">` because React renders in the browser, so I also checked that the JS bundle is served (200). The page in the browser:

![react browser](screenshots/12-browser-react.png)

## 6. Nginx app

```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

| Build | Run |
|---|---|
| ![](screenshots/06-nginx-app-build.png) | ![](screenshots/06-nginx-app-run.png) |

![nginx browser](screenshots/13-browser-nginx.png)

---

## All 6 containers running

![all running](screenshots/07-all-running.png)

## What I learned

- **Image vs container** - the image is the read-only template built from the Dockerfile; a container is a running instance of it.
- `FROM` picks the base image, `WORKDIR` sets the folder, `COPY` adds files, `RUN` executes at build time, `CMD` runs when the container starts, `EXPOSE` documents the port.
- Copying `package.json` / `requirements.txt` **before** the source code lets Docker cache the dependency layer, so rebuilding after a code change is fast.
- `-p 8081:80` maps host port 8081 to port 80 inside the container. Two containers can both use port 80 internally but need different host ports.
- Multi-stage builds (Java, React) keep build tools out of the final image, so it is much smaller.
- `.dockerignore` stops `node_modules` etc. from being sent in the build context.
