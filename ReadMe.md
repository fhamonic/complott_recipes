
    pip install colorama docker jsonschema
    
    docker build -t python-sandbox docker_config/

    docker run --rm -v $PWD/ressources:/app/src/downloaded:ro -v $PWD/output/pcs:/app/output:rw python-sandbox --cpu-rt-runtime=10000000 --memory=100m --network=none --cap-drop


présentation PCS : https://echarts.apache.org/examples/en/editor.html?c=sunburst-drink
composition electorat : https://echarts.apache.org/examples/en/editor.html?c=bar-y-category-stack
PCS par capital économique et symbolique : https://echarts.apache.org/examples/en/editor.html?c=scatter-life-expectancy-timeline