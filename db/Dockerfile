# Use a imagem base oficial do MongoDB
FROM mongo:latest

# Defina um diretório de trabalho para a imagem
WORKDIR /data

# Copie o arquivo de configuração do MongoDB para a imagem
COPY mongod.conf /etc/mongod.conf

# Exponha a porta padrão do MongoDB (27017)
EXPOSE 8080

# Inicie o serviço do MongoDB quando o contêiner for iniciado
CMD ["mongod", "--config", "/etc/mongod.conf"]
