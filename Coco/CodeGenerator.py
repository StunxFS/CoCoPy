import os
from typing import Optional
from pathlib import Path

from .Scanner import Position


class CodeGenerator(object):
	CR = "\r"
	LF = "\n"
	TAB = "\t"
	EOF = -1
	ls = "\n"
	indent_unit = "\t"

	def __init__(self, sourceDir, outputDir, frameDir) -> None:
		self._frameFile = None
		self._outputFile = None
		self.sourceDir = sourceDir
		self.outputDir = outputDir
		self.frameDir = frameDir

	def openFiles(self, frameFileName: str, sourceFileName: str, outputFileName: str, backup: bool = False) -> None:
		if isinstance(frameFileName, str):
			frameFileName = [frameFileName]

		self._frameFile = None
		for frameName in frameFileName:
			fr = self.sourceDir / frameName
			if not fr.is_file():
				if self.frameDir is not None:
					fr = self.frameDir / frameName
			try:
				self._frameFile = fr.open("rt", encoding="utf-8")
				break
			except IOError:
				pass

		if self._frameFile is None:
			raise RuntimeError("-- Compiler Error: Cannot open " + frameFileName[0])

		try:
			fn = self.outputDir / outputFileName
			if backup and fn.is_file():
				backup = fn.parent / (fn.name + ".old")
				if backup.is_file():
					os.remove(str(backup))
				os.rename(fn, str(backup))
			self._outputFile = fn.open("wt", encoding="utf-8")
		except BaseException:
			raise RuntimeError("-- Compiler Error: Cannot create " + str(outputFileName[0]) + ".py")

	def close(self) -> None:
		self._frameFile.close()
		self._outputFile.close()

	def CopyFramePart(self, stop: str) -> None:
		assert isinstance(stop, str)
		last = 0
		startCh = stop[0]
		endOfStopString = len(stop) - 1
		ch = self.frameRead()

		while ch != self.__class__.EOF:
			if ch == startCh:
				i = 0
				if i == endOfStopString:
					return  # stop[0..i] found
				ch = self.frameRead()
				i += 1
				while ch == stop[i]:
					if i == endOfStopString:
						return  # stop[0..i] found
					ch = self.frameRead()
					i += 1
				# stop[0..i-1] found; continue with last read character
				self._outputFile.write(stop[0:i])
			elif ch == self.__class__.LF:
				if last != self.__class__.CR:
					self._outputFile.write("\n")
				last = ch
				ch = self.frameRead()
			elif ch == self.__class__.CR:
				self._outputFile.write("\n")
				last = ch
				ch = self.frameRead()
			else:
				self._outputFile.write(str(ch))
				last = ch
				ch = self.frameRead()
		raise RuntimeError(" -- Compiler Error: incomplete or corrupt parser frame file")

	def CopySourcePart(self, pos: Optional[Position], indent: int, forceOutput: bool = False) -> None:
		if pos is None:
			if forceOutput:
				self.Indent(indent)
				self._outputFile.write("pass")
			return

		code = pos.getSubstring()
		col = pos.col - 1

		lines = code.splitlines(True)
		pos = 0
		if (lines is None) or (len(lines) == 0):
			if forceOutput:
				self.Indent(indent)
				self._outputFile.write("pass")
			return

		while lines[0][pos] in (" ", "\t"):
			col += 1
		newLineList = [lines[0]]
		lines.pop(0)
		if col < 0:
			col = 0
		for line in lines:
			newLineList.append(line[col:])

		for line in newLineList:
			self.Indent(indent)
			self._outputFile.write(line)

		if indent > 0:
			self._outputFile.write("\n")

		return

	def frameRead(self) -> str:
		try:
			return self._frameFile.read(1)
		except IOError:
			# raise RuntimeError('-- Compiler Error: error reading Parser.frame')
			return ParserGen.EOF

	def Indent(self, n: int) -> None:
		assert isinstance(n, int)
		self._outputFile.write(self.__class__.indent_unit * n)

	def Ch(ch):
		if isinstance(self, ch, int):
			ch = str(ch)
		if ch < " " or ch >= str(127) or ch == "'" or ch == "\\":
			return ch
		else:
			return "ord('" + ch + "')"

	def ReportCh(self, ch):
		if isinstance(ch, str):
			ch = ord(ch)
		if ch < ord(" ") or ch >= 127 or ch == ord("'") or ch == ord("\\"):
			return str(ch)
		else:
			return "".join(["'", chr(ch), "'"])

	def ChCond(self, ch, relOpStr="=="):
		if isinstance(ch, str):
			ch = ord(ch)

		if ch < ord(" ") or ch >= 127 or ch == ord("'") or ch == ord("\\"):
			return "".join(["ord(self.ch) ", relOpStr, " ", str(ch)])
		else:
			return "".join(["self.ch ", relOpStr, " '", chr(ch), "'"])

	def write(self, aString: str) -> None:
		self._outputFile.write(aString)
