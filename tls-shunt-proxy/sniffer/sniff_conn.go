package sniffer

import (
	"bytes"
	"errors"
	"io"
	"net"
)

type SniffConn struct {
	net.Conn
	rout         io.Reader
	peeked, read bool
	Type         int
	preData      []byte
	path         string
}

const (
	TypeHttp = iota
	TypeHttp2
	TypeTrojan
	TypeUnknown
)

var (
	httpMethods = [...][]byte{
		[]byte("GET"),
		[]byte("POST"),
		[]byte("HEAD"),
		[]byte("PUT"),
		[]byte("DELETE"),
		[]byte("OPTIONS"),
		[]byte("CONNECT"),
	}
	http2Header = []byte("PRI * HTTP/2.0")
	sep         = []byte(" ")
)

func NewPeekPreDataConn(c net.Conn) *SniffConn {
	s := &SniffConn{Conn: c, rout: c}
	s.Type = s.sniff()
	return s
}

func (c *SniffConn) peekPreData(n int) ([]byte, error) {
	if c.read {
		return nil, errors.New("pre-data must be peek before read")
	}
	if c.peeked {
		return nil, errors.New("can only peek once")
	}
	c.peeked = true
	preDate := make([]byte, n)
	n, err := c.Conn.Read(preDate)
	return preDate[:n], err
}

func (c *SniffConn) Read(p []byte) (int, error) {
	if !c.read {
		c.read = true
		c.rout = io.MultiReader(bytes.NewReader(c.preData), c.Conn)
	}
	return c.rout.Read(p)
}

func (c *SniffConn) sniff() int {
	var err error
	c.preData, err = c.peekPreData(64)
	if err != nil && err != io.EOF {
		return TypeUnknown
	}

	if c.sniffHttp() {
		return TypeHttp
	}

	if c.sniffHttp2() {
		return TypeHttp2
	}

	if c.sniffTrojan() {
		return TypeTrojan
	}

	return TypeUnknown
}

func (c *SniffConn) sniffHttp() bool {
	preDataParts := bytes.Split(c.preData, sep)

	if len(preDataParts) < 2 {
		return false
	}

	for _, m := range httpMethods {
		if bytes.Compare(preDataParts[0], m) == 0 {
			c.path = string(preDataParts[1])
			return true
		}
	}
	return false
}

func (c *SniffConn) sniffHttp2() bool {

	return len(c.preData) >= len(http2Header) &&
		bytes.Compare(c.preData[:len(http2Header)], http2Header) == 0
}

func (c *SniffConn) sniffTrojan() bool {
	if len(c.preData) <= 60 {
		return false
	}

	if c.preData[56] == 0x0D && c.preData[57] == 0x0A {
		if c.preData[58] == 0x01 || c.preData[58] == 0x03 || c.preData[58] == 0x7f {
			if c.preData[59] == 0x01 || c.preData[59] == 0x03 || c.preData[59] == 0x04 {
				return true
			}
		}
	}
	return false
}

func (c *SniffConn) SetPath(path string) {
	preDataParts := bytes.Split(c.preData, sep)
	preDataParts[1] = []byte(path)
	c.preData = bytes.Join(preDataParts, sep)
	c.path = path
}

func (c *SniffConn) GetPath() string {
	return c.path
}
