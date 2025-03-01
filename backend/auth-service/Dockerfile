FROM openjdk:17
WORKDIR /app

# Ensure config directory exists
RUN mkdir -p /app/config/keys

# Copy the JAR dynamically
ARG JAR_FILE=target/auth-service-*.jar
COPY ${JAR_FILE} app.jar

# Expose port
EXPOSE 8080

# Run application with correct config path
ENTRYPOINT ["java", "-jar", "app.jar"]
