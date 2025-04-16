package com.trailmetrics.activities.config;

import com.trailmetrics.activities.dto.ActivitiesDeletedMessage;
import com.trailmetrics.activities.dto.ActivityProcessedMessage;
import com.trailmetrics.activities.dto.ActivityRetryMessage;
import com.trailmetrics.activities.dto.ActivitySyncMessage;
import com.trailmetrics.activities.dto.UserSyncRetryMessage;
import java.util.HashMap;
import java.util.Map;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.annotation.EnableKafka;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaProducerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.core.ProducerFactory;
import org.springframework.kafka.listener.ContainerProperties;
import org.springframework.kafka.listener.DeadLetterPublishingRecoverer;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.kafka.support.serializer.JsonDeserializer;
import org.springframework.kafka.support.serializer.JsonSerializer;
import org.springframework.util.backoff.ExponentialBackOff;

@Configuration
@EnableKafka
public class KafkaConfig {

  @Value("${spring.kafka.bootstrap-servers}")
  private String bootstrapServers;

  @Value("${spring.kafka.consumer.group-id}")
  private String groupId;

  /**
   * Configures the Kafka Consumer to process JSON messages dynamically.
   */
  @Bean
  public ConsumerFactory<String, Object> consumerFactory() {
    Map<String, Object> configProps = new HashMap<>();
    configProps.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
    configProps.put(ConsumerConfig.GROUP_ID_CONFIG, groupId);
    configProps.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
    configProps.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);
    configProps.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
    configProps.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, JsonDeserializer.class);
    configProps.put(JsonDeserializer.TRUSTED_PACKAGES, "*");

    return new DefaultKafkaConsumerFactory<>(
        configProps,
        new StringDeserializer(),
        new JsonDeserializer<>(Object.class));
  }

  /**
   * Configures the Kafka Producer to send JSON messages dynamically.
   */
  @Bean
  public ProducerFactory<String, Object> producerFactory() {
    Map<String, Object> configProps = new HashMap<>();
    configProps.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
    configProps.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
    configProps.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);
    return new DefaultKafkaProducerFactory<>(configProps);
  }

  /**
   * Generic Kafka template that supports multiple message types.
   */
  @Bean
  public KafkaTemplate<String, Object> kafkaTemplate() {
    return new KafkaTemplate<>(producerFactory());
  }

  /**
   * Creates a strongly-typed KafkaTemplate for ActivitySyncMessage.
   */
  @Bean
  public KafkaTemplate<String, ActivitySyncMessage> activitySyncKafkaTemplate() {
    ProducerFactory<String, ActivitySyncMessage> factory =
        new DefaultKafkaProducerFactory<>(producerFactory().getConfigurationProperties());
    return new KafkaTemplate<>(factory);
  }

  /**
   * Creates a strongly-typed KafkaTemplate for UserSyncRetryMessage.
   */
  @Bean
  public KafkaTemplate<String, UserSyncRetryMessage> userRetrySyncKafkaTemplate() {
    ProducerFactory<String, UserSyncRetryMessage> factory =
        new DefaultKafkaProducerFactory<>(producerFactory().getConfigurationProperties());
    return new KafkaTemplate<>(factory);
  }

  /**
   * Creates a strongly-typed KafkaTemplate for ActivityRetryMessage.
   */
  @Bean
  public KafkaTemplate<String, ActivityRetryMessage> activityRetryKafkaTemplate() {
    ProducerFactory<String, ActivityRetryMessage> factory =
        new DefaultKafkaProducerFactory<>(producerFactory().getConfigurationProperties());
    return new KafkaTemplate<>(factory);
  }

  /**
   * Creates a strongly-typed KafkaTemplate for ActivityProcessedMessage.
   */
  @Bean
  public KafkaTemplate<String, ActivityProcessedMessage> activityProcessedKafkaTemplate() {
    ProducerFactory<String, ActivityProcessedMessage> factory =
        new DefaultKafkaProducerFactory<>(producerFactory().getConfigurationProperties());
    return new KafkaTemplate<>(factory);
  }

  /**
   * Creates a strongly-typed KafkaTemplate for ActivitiesDeletedMessage.
   */
  @Bean
  public KafkaTemplate<String, ActivitiesDeletedMessage> userActivityChangesKafkaTemplate() {
    ProducerFactory<String, ActivitiesDeletedMessage> factory =
        new DefaultKafkaProducerFactory<>(producerFactory().getConfigurationProperties());
    return new KafkaTemplate<>(factory);
  }


  /**
   * Creates a Kafka listener factory with manual acknowledgment and exponential backoff retry.
   */
  @Bean
  public ConcurrentKafkaListenerContainerFactory<String, Object> kafkaListenerContainerFactory(
      KafkaTemplate<String, Object> kafkaTemplate) {
    ConcurrentKafkaListenerContainerFactory<String, Object> factory =
        new ConcurrentKafkaListenerContainerFactory<>();
    factory.setConsumerFactory(consumerFactory());
    factory.setBatchListener(false);
    factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL);

    // Add Exponential Backoff Retry with DefaultErrorHandler
    factory.setCommonErrorHandler(new DefaultErrorHandler(
        new DeadLetterPublishingRecoverer(kafkaTemplate),
        new ExponentialBackOff(15000, 2.0) // Initial delay: 15s, multiplier: 2x
    ));

    return factory;
  }


}
