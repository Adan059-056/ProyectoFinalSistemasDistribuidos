import os
import subprocess
import argparse
import sys

def split_video(input_path, output_dir, num_fragments=10, overwrite=False):
    # Verificar si el archivo de entrada existe
    if not os.path.exists(input_path):
        print(f"Error: Archivo de entrada no encontrado: {input_path}")
        sys.exit(1)
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Obtener duración del video
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]
        duration = float(subprocess.check_output(cmd).decode().strip())
    except Exception as e:
        print(f"Error obteniendo duración del video: {e}")
        sys.exit(1)
    
    fragment_duration = duration / num_fragments
    
    # Dividir el video en fragmentos
    for i in range(num_fragments):
        start_time = i * fragment_duration
        output_path = os.path.join(output_dir, f"fragment_{i+1}.mp4")
        
        # Saltar si el fragmento ya existe y no se fuerza sobreescritura
        if os.path.exists(output_path) and not overwrite:
            print(f"Fragmento {i+1} ya existe. Saltando...")
            continue
        
        try:
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-ss", str(start_time),
                "-t", str(fragment_duration),
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                output_path
            ]
            subprocess.run(cmd, check=True)
            print(f"Fragmento {i+1} generado: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error generando fragmento {i+1}: {e}")
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Divide un video en fragmentos')
    parser.add_argument('input', help='Ruta al video de entrada')
    parser.add_argument('output', help='Directorio de salida para fragmentos')
    parser.add_argument('-n', '--num', type=int, default=10, help='Número de fragmentos')
    parser.add_argument('--overwrite', action='store_true', help='Sobreescribir fragmentos existentes')
    
    args = parser.parse_args()
    split_video(args.input, args.output, args.num, args.overwrite)

    