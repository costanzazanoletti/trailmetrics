package com.trailmetrics.activities.service;

import com.trailmetrics.activities.model.Activity;
import com.trailmetrics.activities.model.ActivityStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;

@Service
@RequiredArgsConstructor
public class GpxStreamExtractorService {

  public List<ActivityStream> extractStreamsFromGpx(InputStream inputStream, Activity activity) {
    List<List<Double>> latlng = new ArrayList<>();
    List<Double> altitude = new ArrayList<>();
    List<Double> distance = new ArrayList<>();
    List<Double> grade = new ArrayList<>();

    try {
      DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
      factory.setNamespaceAware(true);
      DocumentBuilder builder = factory.newDocumentBuilder();
      Document doc = builder.parse(new InputSource(inputStream));
      NodeList trackPoints = doc.getElementsByTagNameNS("*", "trkpt");

      double cumulativeDistance = 0.0;
      distance.add(0.0); // First point
      grade.add(0.0);

      for (int i = 0; i < trackPoints.getLength(); i++) {
        Element trackPoint = (Element) trackPoints.item(i);
        double lat = Double.parseDouble(trackPoint.getAttribute("lat"));
        double lon = Double.parseDouble(trackPoint.getAttribute("lon"));
        latlng.add(List.of(lat, lon));

        double ele = 0.0;
        NodeList eleNodes = trackPoint.getElementsByTagNameNS("*", "ele");
        if (eleNodes.getLength() > 0) {
          ele = Double.parseDouble(eleNodes.item(0).getTextContent());
          altitude.add(ele);
        } else {
          altitude.add(null);
        }

        if (i > 0 && altitude.get(i) != null && altitude.get(i - 1) != null) {
          double d = haversine(
              latlng.get(i - 1).get(0), latlng.get(i - 1).get(1),
              lat, lon
          );
          cumulativeDistance += d;
          distance.add(cumulativeDistance);

          double elevDiff = altitude.get(i) - altitude.get(i - 1);
          double g = (d > 0) ? (elevDiff / d * 100.0) : 0.0;
          grade.add(g);
        }
      }

      List<ActivityStream> streams = new ArrayList<>();
      streams.add(createStream("latlng", latlng, activity));
      streams.add(createStream("altitude", altitude, activity));
      streams.add(createStream("distance", distance, activity));
      streams.add(createStream("grade_smooth", grade, activity));

      return streams;

    } catch (Exception e) {
      throw new RuntimeException("Error parsing GPX File", e);
    }
  }

  // Haversine in meters
  private double haversine(double lat1, double lon1, double lat2, double lon2) {
    final int R = 6371000; // Earth radius in meters
    double dLat = Math.toRadians(lat2 - lat1);
    double dLon = Math.toRadians(lon2 - lon1);
    double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
    double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  private ActivityStream createStream(String type, List<?> data, Activity activity) {
    ActivityStream stream = new ActivityStream();
    stream.setActivity(activity);
    stream.setType(type);
    stream.setSeriesType("distance");
    stream.setResolution("high");
    stream.setOriginalSize(data.size());
    stream.setDataFromList(new ArrayList<>(data));
    return stream;
  }

}
