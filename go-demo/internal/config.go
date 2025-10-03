package internal

import (
	"os"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Server struct {
		Address       string `yaml:"address"`
		Insecure      bool   `yaml:"insecure"`
		Authorization string `yaml:"authorization"`
	} `yaml:"server"`
	Stream struct {
		Type string `yaml:"type"`
	} `yaml:"stream"`
	Filters struct {
		Programs  []string `yaml:"programs"`
		Pools     []string `yaml:"pools"`
		Tokens    []string `yaml:"tokens"`
		Traders   []string `yaml:"traders"`
		Senders   []string `yaml:"senders"`
		Receivers []string `yaml:"receivers"`
		Addresses []string `yaml:"addresses"`
		Signers   []string `yaml:"signers"`
	} `yaml:"filters"`
}

func LoadConfig(configPath string) (*Config, error) {
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}

	var config Config
	err = yaml.Unmarshal(data, &config)
	if err != nil {
		return nil, err
	}

	return &config, nil
}
