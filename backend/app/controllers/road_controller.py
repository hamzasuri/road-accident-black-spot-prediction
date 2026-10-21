import json
from backend.app.db import get_connection

def get_roads():
    conn=get_connection()
    cursor = conn.cursor()
    

    cursor.execute("""
        SELECT
            id,
            u,
            v,
            key,
            road_length,
            highway,
            lanes,
            maxspeed,
            oneway,
            risk_score,
            risk_level,
            prediction_confidence,
            ST_AsGeoJSON(geometry) AS geometry
        FROM road_segments
        ORDER BY id;
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "id": row[0],
            "u": row[1],
            "v": row[2],
            "key": row[3],
            "road_length": row[4],
            "highway": row[5],
            "lanes": row[6],
            "maxspeed": row[7],
            "oneway": row[8],
            "risk_score": float(row[9]) if row[9] is not None else None,
            "risk_level": row[10],
            "prediction_confidence": float(row[11]) if row[11] is not None else None,
            "geometry": json.loads(row[12]) if row[12] is not None else None
        }
        for row in rows
    ]