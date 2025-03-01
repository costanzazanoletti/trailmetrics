FROM openjdk:17
WORKDIR /app

# Copy the JAR dynamically
ARG JAR_FILE=target/activity-service-*.jar
COPY ${JAR_FILE} app.jar

# Expose port
EXPOSE 8081

# Run application with default Spring Boot config locations
ENTRYPOINT ["java", "-jar", "app.jar"]
