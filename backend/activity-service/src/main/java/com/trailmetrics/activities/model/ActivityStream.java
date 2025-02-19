package com.trailmetrics.activities.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.io.IOException;
import java.util.List;
import lombok.Data;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "activity_streams")
@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ActivityStream {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne
  @JoinColumn(name = "activity_id", nullable = false)
  private Activity activity;

  @Column(name = "type")
  private String type;

  @Column(name = "data", columnDefinition = "json")
  @JdbcTypeCode(SqlTypes.JSON) // This tells Hibernate to store this as JSON
  private String data; // Store raw JSON as a string

  @Column(name = "series_type")
  private String seriesType;

  @Column(name = "original_size")
  private int originalSize;

  @Column(name = "resolution")
  private String resolution;

  /**
   * Convert JSON string to List<Object>
   */
  public List<Object> getDataAsList() {
    try {
      ObjectMapper objectMapper = new ObjectMapper();
      return objectMapper.readValue(data, new TypeReference<List<Object>>() {
      });
    } catch (IOException e) {
      throw new RuntimeException("Failed to parse JSON data", e);
    }
  }

  /**
   * Convert List<Object> to JSON string
   */
  public void setDataFromList(List<Object> dataList) {
    try {
      ObjectMapper objectMapper = new ObjectMapper();
      this.data = objectMapper.writeValueAsString(dataList);
    } catch (IOException e) {
      throw new RuntimeException("Failed to convert list to JSON", e);
    }
  }
}
