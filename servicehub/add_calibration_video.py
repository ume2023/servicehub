"""
Add a calibration video to the site.

HOW TO USE:
1. Upload your calibration video to YouTube (can be "Unlisted" so it's not
   publicly searchable, but still viewable by anyone with the link/embedded).
2. Get the video's EMBED link:
   - On YouTube, open the video -> Share -> Embed -> copy the "src" URL
     (looks like: https://www.youtube.com/embed/XXXXXXXXXXX)
3. Edit the values below.
4. Run:  python add_calibration_video.py
"""

from app import app, db, CalibrationVideo

with app.app_context():
    video = CalibrationVideo(
        title="How to calibrate the pressure sensor",     # <-- change this
        description="Step-by-step walkthrough, 5 minutes.",  # <-- change this
        video_url="https://www.youtube.com/embed/YOUR_VIDEO_ID",  # <-- change this
    )
    db.session.add(video)
    db.session.commit()
    print(f"Added calibration video: {video.title} (id={video.id})")
