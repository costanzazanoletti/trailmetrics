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

    try {
      DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
      factory.setNamespaceAware(true);
      DocumentBuilder builder = factory.newDocumentBuilder();
      Document doc = builder.parse(new InputSource(inputStream));

      NodeList trackPoints = doc.getElementsByTagNameNS("*", "trkpt");

      for (int i = 0; i < trackPoints.getLength(); i++) {
        Element trackPoint = (Element) trackPoints.item(i);
        double lat = Double.parseDouble(trackPoint.getAttribute("lat"));
        double lon = Double.parseDouble(trackPoint.getAttribute("lon"));
        latlng.add(List.of(lat, lon));

        NodeList eleNodes = trackPoint.getElementsByTagNameNS("*", "ele");
        if (eleNodes.getLength() > 0) {
          double ele = Double.parseDouble(eleNodes.item(0).getTextContent());
          altitude.add(ele);
        } else {
          altitude.add(null); // match index
        }
      }

      List<ActivityStream> streams = new ArrayList<>();

      if (!latlng.isEmpty()) {
        ActivityStream latlngStream = new ActivityStream();
        latlngStream.setActivity(activity);
        latlngStream.setType("latlng");
        latlngStream.setSeriesType("distance");
        latlngStream.setResolution("high");
        latlngStream.setOriginalSize(latlng.size());
        latlngStream.setDataFromList(new ArrayList<>(latlng));
        streams.add(latlngStream);
      }

      if (!altitude.isEmpty()) {
        ActivityStream altStream = new ActivityStream();
        altStream.setActivity(activity);
        altStream.setType("altitude");
        altStream.setSeriesType("distance");
        altStream.setResolution("high");
        altStream.setOriginalSize(altitude.size());
        altStream.setDataFromList(new ArrayList<>(altitude));
        streams.add(altStream);
      }

      return streams;

    } catch (Exception e) {
      throw new RuntimeException("Error parsing GPX File", e);
    }
  }
}
