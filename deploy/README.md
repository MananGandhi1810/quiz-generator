# Deploy to quizgen.manan.cloud

This setup assumes a Linux VPS running Docker Compose and host Nginx. Host Nginx handles HTTPS; Docker serves the application on localhost:8080. If you already use another reverse proxy, forward this domain to localhost:8080 using its HTTPS setup instead.

1. Create a DNS **A record** for `quizgen.manan.cloud` pointing to your server's public IPv4 address. Only add an AAAA record if the server is reachable over IPv6. Allow inbound TCP ports **80 and 443** in the server firewall and cloud firewall.
2. Copy this project to the server, for example `/opt/quiz-generator`. Keep `.env` private (`chmod 600 .env`). Configure `GEMINI_API_KEY`, `PORT=8080`, and `BIND_ADDRESS=127.0.0.1` in `.env`.
3. From the project directory, start the application:

   ```sh
   docker compose up --build -d
   docker compose ps
   curl --fail http://127.0.0.1:8080/api/health
   ```

4. On Debian/Ubuntu, install host Nginx and Certbot, then enable the provided domain configuration:

   ```sh
   sudo apt-get update
   sudo apt-get install nginx certbot python3-certbot-nginx
   sudo cp deploy/quizgen.manan.cloud.conf /etc/nginx/sites-available/quizgen.manan.cloud
   sudo ln -s /etc/nginx/sites-available/quizgen.manan.cloud /etc/nginx/sites-enabled/quizgen.manan.cloud
   sudo nginx -t
   sudo systemctl reload nginx
   ```

   Run the symlink command once. If a site for this domain already exists, update that configuration instead of enabling a duplicate. Keep other domain configurations in place.

5. Once DNS points to this server and HTTP is reachable, request HTTPS:

   ```sh
   sudo certbot --nginx -d quizgen.manan.cloud --redirect
   sudo certbot renew --dry-run
   ```

   Certbot asks for your contact email and agreement to its terms. Its Nginx plugin updates the installed domain configuration with the certificate and HTTP-to-HTTPS redirect. Check that your installation enables automatic renewal (`systemctl list-timers --all | grep certbot` on systems using systemd). Certificate issuance is performed on your server, not by this repository.

6. Open **https://quizgen.manan.cloud**, upload `examples/study-notes.pdf`, and generate a quiz. Check `https://quizgen.manan.cloud/api/health` if diagnosing routing issues.

The Gemini key stays in the backend. Uploads support the same 10 MB limit and long OCR/generation timeout through both Nginx layers. The app is publicly accessible and every generation uses your Gemini quota; this version does not include user accounts. If access should be private, configure access restrictions in your reverse proxy.

For updates, copy updated sources and run `docker compose up --build -d` again. Use `docker compose logs --tail=100` for diagnostics. If changing `PORT`, also change the upstream port in the host Nginx configuration.

Reference: [Certbot Nginx installation and HTTPS setup](https://certbot.eff.org/instructions), [Certbot renewal documentation](https://eff-certbot.readthedocs.io/en/stable/using.html#renewing-certificates).
