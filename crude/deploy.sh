docker compose build && docker save memmaker/crude > crude_image.tar && scp crude_image.tar mgdx.net: && rm crude_image.tar

ssh mgdx.net "cd ~/ServerTools/Crude && docker compose down && docker image rm memmaker/crude && docker load < ~/crude_image.tar && docker compose up -d && rm ~/crude_image.tar"