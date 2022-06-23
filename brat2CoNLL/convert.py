# Convert files from brat annotated format to CoNLL format
import os.path
from os import listdir, path
from collections import namedtuple
import argparse
from pathlib import Path


class Brat2ConnlConverter:
    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = input_dir

        if not os.path.exists(input_dir) or not os.path.isdir(input_dir):
            raise Exception("The input directory does not exists or is not a directory")

        self.output_dir = output_dir

        if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
            raise Exception("The output directory does not exists or is not a directory")

    def read_input(self, annotation_file: str, text_file: str):
        """Read the input BRAT files into python data structures
        Parameters
            annotation_file:
                BRAT formatted annotation file
            text_file:
                Corresponding file containing the text as a string
        Returns
            input_annotations: list
                A list of dictionaries in which each entry corresponds to one line of the annotation file
            text_string: str
                Input text read from text file
        """
        with open(text_file, 'r') as f:
            text_string = f.read()
        input_annotations = []
        # Read each line of the annotation file to a dictionary
        with open(annotation_file, 'r') as fi:
            for line in fi:
                annotation_record = {}
                entry = line.split()
                type = entry[0]
                if not type.startswith("T"):
                    continue
                annotation_record["label"] = entry[1]
                annotation_record["start"] = int(entry[2])
                annotation_record["end"] = int(entry[3])
                annotation_record["text"] = ' '.join(entry[4:])
                input_annotations.append(annotation_record)
        # Annotation file need not be sorted by start position so sort explicitly. Can also be done using end position
        input_annotations = sorted(input_annotations, key=lambda x: x["start"])

        return input_annotations, text_string

    def process(self):
        """Loop over all annotation files, and write tokens with their label to an output file"""
        file_pair_list = self.read_input_folder()

        for file_count, file_pair in enumerate(file_pair_list):
            annotation_file, text_file = file_pair.ann, file_pair.text
            converted = self.convert_file(annotation_file, text_file)

            output_file = Path(text_file).name.replace(".txt", ".conll")
            with open(os.path.join(self.output_dir, output_file), 'w') as fo:
                for token, label in converted:
                    if token == "\n":
                        fo.write("\n")
                    fo.write(f'{token} {label}\n')


    def convert_file(self, annotation_file, text_file) -> list:
        output_stream = []
        input_annotations, text_string = self.read_input(annotation_file, text_file)
        text_tokens = text_string.split()
        annotation_count = 0
        current_ann_start = input_annotations[annotation_count]["start"]
        current_ann_end = input_annotations[annotation_count]["end"]
        num_annotations = len(input_annotations)
        current_index = 0
        num_tokens = len(text_tokens)

        i = 0  # Initialize Token number
        while i < num_tokens:
            if current_index != current_ann_start:
                label = 'O'
                output_stream.append((f'{text_tokens[i]}', f'{label}'))
                current_index += len(text_tokens[i]) + 1
                i += 1
            else:
                label = input_annotations[annotation_count]["label"]

                first = True
                while current_index <= current_ann_end and i < num_tokens:
                    prefix = "I-"
                    if first:
                        first = False
                        prefix = "B-"
                    output_stream.append((f'{text_tokens[i]}', f'{prefix}{label}'))
                    current_index += len(text_tokens[i]) + 1
                    i += 1
                annotation_count += 1
                if annotation_count < num_annotations:
                    current_ann_start = input_annotations[annotation_count]["start"]
                    current_ann_end = input_annotations[annotation_count]["end"]

        output_stream.append(("\n",""))

        return output_stream

    # def write_output(self):
    #     """Read input from a single file and write the output"""
    #     input_annotations, text_string = self.read_input(annotation_file, text_file)
    #     self.parse_text(input_annotations, text_string)

    def read_input_folder(self):
        """Read multiple annotation files from a given input folder"""
        file_list = listdir(self.input_dir)
        annotation_files = sorted([file for file in file_list if file.endswith('.ann')])

        file_pair_list = []
        file_pair = namedtuple('file_pair', ['ann', 'text'])
        # The folder is assumed to contain *.ann and *.txt files with the 2 files of a pair having the same file name
        for file in annotation_files:
            if file.replace('.ann', '.txt') in file_list:
                file_pair_list.append(
                    file_pair(path.join(self.input_dir, file), path.join(self.input_dir, file.replace('.ann', '.txt'))))
            else:
                raise f"{file} does not have a corresponding text file"

        return file_pair_list


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input directory where Brat annotations are stored",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory where CoNLL 2002 format annotations are saved",
    )

    args = parser.parse_args()
    format_convertor = Brat2ConnlConverter(args.input, args.output)
    format_convertor.process()
