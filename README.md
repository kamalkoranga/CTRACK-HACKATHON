# 📘 CTRACK – Journey Tracker for Students & Developers

**CTrack** is a minimal tool for students and developers to document and track their learning journey. Log daily progress, set milestones, and reflect on your growth — all in one place.

## 🚀 Features

- Track daily/weekly learning logs
- Set and manage goals/milestones
- Add reflections or notes
- View visual progress (timeline or chart)
- Simple, clean, and privacy-first

## 🌐 Live Demo

🔗 [Live URL](https://ctrack-hackathon-e93l.onrender.com)
> ⚠️ Note: The site may load slowly as it's hosted on Render (free tier) with a Supabase backend. Performance may vary.

## 🛠️ Tech Stack

- Frontend: [html, css, js]
- Backend: [Python, Flask]
- Database: [Supabase]
- UI: [BootstrapCSS]

## 🧑‍💻 Team Members

- [Kamal Koranga](https://github.com/kamalkoranga) – Full-stack Developer
- [Shubham Rawat]() – Frontend Developer
- [Sanchi]() – UI / UX Developer

## 🏁 Built At
This project was created during [24 Hr Hackathon], at GEHU Haldwani inspired by the need for a focused space to track developer and student learning paths — like a portfolio, but centered on growth and progress.

### ElasticSearch docker container:
docker run --name elasticsearch -d --rm -p 9200:9200 --memory="2GB" -e discovery.type=single-node -e xpack.security.enabled=false -t docker.elastic.co/elasticsearch/elasticsearch:9.0.3