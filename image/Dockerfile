FROM public.ecr.aws/lambda/python:3.11

# copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# required to make sqllite3 work for Chroma (typically outdated version)
RUN pip install pysqlite3-binary

# install the specified packages
RUN pip install --no-cache-dir -r requirements.txt

# for local testing
EXPOSE 8000

# set IS_USING_IMAGE_RUNTIME Environment variable
ENV IS_USING_IMAGE_RUNTIME=True

# copy all files in ./src
COPY src/* ${LAMBDA_TASK_ROOT}
COPY src/rag_app ${LAMBDA_TASK_ROOT}/rag_app
COPY src/data/chroma ${LAMBDA_TASK_ROOT}/data/chroma
