<?xml version="1.0" encoding="ISO-8859-1"?>
<StyledLayerDescriptor version="1.0.0"
 xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"
 xmlns="http://www.opengis.net/sld"
 xmlns:ogc="http://www.opengis.net/ogc"
 xmlns:xlink="http://www.w3.org/1999/xlink"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NamedLayer>
    <Name>sectors</Name>
    <UserStyle>
      <Title>Sector</Title>
      <Abstract></Abstract>
      <FeatureTypeStyle>
        <Rule>
          <Name>sector</Name>
          <Title>Sector</Title>
          <Abstract>Sector for counter measure</Abstract>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill"><ogc:PropertyName>color</ogc:PropertyName></CssParameter>
              <CssParameter name="fill-opacity">0.5</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke"><ogc:PropertyName>color</ogc:PropertyName></CssParameter>
              <CssParameter name="stroke-width">1.2</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <TextSymbolizer>
            <Label>
              <ogc:PropertyName>sectorname</ogc:PropertyName>
            </Label>
            <Font>
              <!--<CssParameter name="font-family">Arial</CssParameter>-->
              <CssParameter name="font-family">SansSerif</CssParameter>
              <CssParameter name="font-size">12</CssParameter>
              <CssParameter name="font-style">normal</CssParameter>
              <!--<CssParameter name="font-weight">bold</CssParameter>-->
            </Font>
            <Halo>
              <Radius>3</Radius>
              <Fill>
                <CssParameter name="fill">#ffffff</CssParameter>
              </Fill>
            </Halo>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.5</AnchorPointY>
                </AnchorPoint>
              </PointPlacement>
            </LabelPlacement>
            <Fill>
              <!--<CssParameter name="fill"><ogc:PropertyName>color</ogc:PropertyName></CssParameter>-->
              <CssParameter name="fill">#000000</CssParameter>
            </Fill>
          </TextSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
