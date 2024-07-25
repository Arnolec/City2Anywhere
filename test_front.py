import folium.elements
import streamlit as st
import folium
import branca
from streamlit_folium import st_folium

@st.cache_data
def init():
    i = 0
    return i

def increase():
    i += 1
    print('AZEAIO')

i = init()

st.write(i)
html="""
    <script type="module" src="script.js">
    const { spawn } = import child_process from 'child_process';

    // Run a Python script and return output
    function runPythonScript(scriptPath, args) {

    // Use child_process.spawn method from 
    // child_process module and assign it to variable
    const pyProg = spawn('python', [scriptPath].concat(args));
    console.log('Running Python script...);
    // Collect data from script and print to console
    let data = '';
    pyProg.stdout.on('data', (stdout) => {
        data += stdout.toString();
    });

    // Print errors to console, if any
    pyProg.stderr.on('data', (stderr) => {
        console.log(`stderr: ${stderr}`);
    });

    // When script is finished, print collected data
    pyProg.on('close', (code) => {
        console.log(`child process exited with code ${code}`);
        console.log(data);
    });
    }

    // Run the Python file
    runPythonScript('./pythont.py', []);
    </script>

    """
m = folium.Map()

iframe = branca.element.IFrame(html=html)
popup = folium.Popup(iframe, parse_html= True, max_width=2650)

folium.Marker([30,-100], popup=popup).add_to(m)

map = st_folium(
    m, center=[30,-100], zoom=8, height=600, width=1000, key="new"
)
