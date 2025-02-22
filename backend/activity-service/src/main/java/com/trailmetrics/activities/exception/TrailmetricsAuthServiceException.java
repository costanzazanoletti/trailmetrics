package com.trailmetrics.activities.exception;

public class TrailmetricsAuthServiceException extends RuntimeException {

  public TrailmetricsAuthServiceException(String message, Throwable cause) {
    super(message, cause);
  }

  public TrailmetricsAuthServiceException(String message) {
    super(message);
  }
}
