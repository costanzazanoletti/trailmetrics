package com.trailmetrics.activities.response;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

public class ApiResponseFactory {

  // Success with data and optional message
  public static <T> ResponseEntity<ApiResponse<T>> ok(T data, String message) {
    return ResponseEntity.ok(new ApiResponse<>(true, data, message));
  }

  public static <T> ResponseEntity<ApiResponse<T>> ok(T data) {
    return ResponseEntity.ok(new ApiResponse<>(true, data, "Success"));
  }

  // Generic success with no data
  public static <T> ResponseEntity<ApiResponse<T>> ok() {
    return ResponseEntity.ok(new ApiResponse<>(true, null, "Success"));
  }

  // Error with message and optional status
  public static <T> ResponseEntity<ApiResponse<T>> error(String message, HttpStatus status) {
    return ResponseEntity.status(status).body(new ApiResponse<>(false, null, message));
  }

  public static <T> ResponseEntity<ApiResponse<T>> error(String message) {
    return error(message, HttpStatus.INTERNAL_SERVER_ERROR);
  }
}
