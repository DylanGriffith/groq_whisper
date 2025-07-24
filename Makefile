SERVER = ${HOMEASSISTANT_SERVER}

install:
	scp -r custom_components/groq_whisper ${SERVER}:/root/config/custom_components/groq_whisper
