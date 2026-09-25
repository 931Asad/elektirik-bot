import io
from staticmap import StaticMap, CircleMarker, Line


def render_line_map(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> io.BytesIO:
    """Boshi va oxiri berilgan liniyani OSM xaritasi ustiga chizib, PNG bytes qaytaradi."""
    m = StaticMap(900, 650, url_template="https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")

    # chiziq (boshi -> oxiri)
    line = Line(
        [(start_lon, start_lat), (end_lon, end_lat)],
        "#2b6cff",
        4,
    )
    m.add_line(line)

    # boshlanish nuqtasi - yashil
    m.add_marker(CircleMarker((start_lon, start_lat), "#22b14c", 14))
    # oxirgi nuqta - qizil
    m.add_marker(CircleMarker((end_lon, end_lat), "#e02020", 14))

    image = m.render()
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "liniya.png"
    return buf
