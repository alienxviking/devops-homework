# build stage - compile with the JDK
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /src
COPY HelloWorld.java .
RUN javac HelloWorld.java

# run stage - only the JRE + compiled class
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /src/*.class .
EXPOSE 8080
CMD ["java", "HelloWorld"]
